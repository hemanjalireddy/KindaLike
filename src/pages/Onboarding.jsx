import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  searchRestaurants,
  submitOnboarding,
  startExtraction,
  getExtractionStatus,
  submitQuestionnaire,
  getCurrentUser
} from '../services/api'

function Onboarding() {
  const navigate = useNavigate()
  const currentUser = getCurrentUser()

  // Step: 'search' | 'details' | 'extracting' | 'questionnaire'
  const [step, setStep] = useState('search')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Search state
  const [searchName, setSearchName] = useState('')
  const [searchLocation, setSearchLocation] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [selectedRestaurants, setSelectedRestaurants] = useState([])

  // Details state
  const [restaurantDetails, setRestaurantDetails] = useState({})

  // Extraction state
  const [extractionStatus, setExtractionStatus] = useState(null)
  const [extractionProgress, setExtractionProgress] = useState(0)

  // Questionnaire state
  const [questionnaire, setQuestionnaire] = useState(null)
  const [answers, setAnswers] = useState({})

  // Search for restaurants
  const handleSearch = async () => {
    if (!searchName.trim() || !searchLocation.trim()) {
      setError('Please enter both restaurant name and location')
      return
    }

    setLoading(true)
    setError('')

    try {
      const results = await searchRestaurants(searchName.trim(), searchLocation.trim())
      setSearchResults(results)
      if (results.length === 0) {
        setError('No restaurants found. Try different search terms.')
      }
    } catch (err) {
      setError(err.message || 'Failed to search restaurants')
    } finally {
      setLoading(false)
    }
  }

  // Select a restaurant
  const handleSelectRestaurant = (restaurant) => {
    if (selectedRestaurants.length >= 3) {
      setError('You can only select 3 restaurants')
      return
    }

    if (selectedRestaurants.find(r => r.yelp_id === restaurant.yelp_id)) {
      return // Already selected
    }

    setSelectedRestaurants([...selectedRestaurants, restaurant])
    setError('')
  }

  // Remove a selected restaurant
  const handleRemoveRestaurant = (yelpId) => {
    setSelectedRestaurants(selectedRestaurants.filter(r => r.yelp_id !== yelpId))
    const newDetails = { ...restaurantDetails }
    delete newDetails[yelpId]
    setRestaurantDetails(newDetails)
  }

  // Update restaurant details (notes, favorite dish)
  const handleDetailChange = (yelpId, field, value) => {
    setRestaurantDetails({
      ...restaurantDetails,
      [yelpId]: {
        ...restaurantDetails[yelpId],
        [field]: value
      }
    })
  }

  // Proceed to details step
  const handleProceedToDetails = () => {
    if (selectedRestaurants.length !== 3) {
      setError('Please select exactly 3 restaurants')
      return
    }
    setStep('details')
    setError('')
  }

  // Submit onboarding and start extraction
  const handleSubmitOnboarding = async () => {
    setLoading(true)
    setError('')

    try {
      // Format restaurants for API
      const restaurants = selectedRestaurants.map((r, index) => ({
        yelp_id: r.yelp_id,
        google_place_id: r.google_place_id || null,
        name: r.name,
        location: searchLocation,
        selection_order: index + 1,
        user_notes: restaurantDetails[r.yelp_id]?.notes || null,
        favorite_dish: restaurantDetails[r.yelp_id]?.favorite_dish || null
      }))

      await submitOnboarding(restaurants)
      setStep('extracting')

      // Start extraction
      const extractionResult = await startExtraction()

      if (extractionResult.status === 'awaiting_questionnaire' && extractionResult.questionnaire) {
        setQuestionnaire(extractionResult.questionnaire)
        setStep('questionnaire')
      } else {
        // Poll for status
        pollExtractionStatus()
      }
    } catch (err) {
      setError(err.message || 'Failed to submit preferences')
      setStep('details')
    } finally {
      setLoading(false)
    }
  }

  // Poll extraction status
  const pollExtractionStatus = useCallback(async () => {
    try {
      const status = await getExtractionStatus()
      setExtractionStatus(status.status)
      setExtractionProgress(status.progress_percent || 0)

      if (status.status === 'completed' || status.status === 'awaiting_questionnaire') {
        // Try to get questionnaire
        const extractionResult = await startExtraction()
        if (extractionResult.questionnaire) {
          setQuestionnaire(extractionResult.questionnaire)
          setStep('questionnaire')
        } else {
          // No questionnaire, go directly to chatbot
          navigate('/chatbot')
        }
      } else if (status.status === 'failed') {
        setError('Preference extraction failed. Please try again.')
        setStep('details')
      } else {
        // Continue polling
        setTimeout(pollExtractionStatus, 2000)
      }
    } catch (err) {
      console.error('Polling error:', err)
      setTimeout(pollExtractionStatus, 3000)
    }
  }, [navigate])

  // Handle questionnaire answer
  const handleAnswerChange = (questionId, value) => {
    setAnswers({
      ...answers,
      [questionId]: value
    })
  }

  // Submit questionnaire
  const handleSubmitQuestionnaire = async () => {
    setLoading(true)
    setError('')

    try {
      const formattedAnswers = Object.entries(answers).map(([questionId, value]) => ({
        question_id: questionId,
        answer_value: value
      }))

      await submitQuestionnaire(formattedAnswers)
      navigate('/chatbot')
    } catch (err) {
      setError(err.message || 'Failed to submit questionnaire')
    } finally {
      setLoading(false)
    }
  }

  // Render search step
  const renderSearchStep = () => (
    <div className="onboarding-step">
      <h3>Search for your favorite restaurants</h3>
      <p className="step-description">
        Tell us about 3 restaurants you love. We'll use these to understand your preferences.
      </p>

      <div className="search-form">
        <input
          type="text"
          placeholder="Restaurant name"
          value={searchName}
          onChange={(e) => setSearchName(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        <input
          type="text"
          placeholder="City, State (e.g., Ithaca, NY)"
          value={searchLocation}
          onChange={(e) => setSearchLocation(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        <button onClick={handleSearch} disabled={loading} className="btn-primary">
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {/* Search Results */}
      {searchResults.length > 0 && (
        <div className="search-results">
          <h4>Search Results</h4>
          <div className="results-grid">
            {searchResults.map((restaurant) => {
              const isSelected = selectedRestaurants.find(r => r.yelp_id === restaurant.yelp_id)
              return (
                <div key={restaurant.yelp_id} className={`restaurant-search-card ${isSelected ? 'selected' : ''}`}>
                  {restaurant.image_url && (
                    <img src={restaurant.image_url} alt={restaurant.name} className="restaurant-thumb" />
                  )}
                  <div className="restaurant-search-info">
                    <h5>{restaurant.name}</h5>
                    <div className="restaurant-meta">
                      {restaurant.rating && <span className="rating">{'★'.repeat(Math.round(restaurant.rating))} {restaurant.rating}</span>}
                      {restaurant.price_level && <span className="price">{'$'.repeat(restaurant.price_level)}</span>}
                    </div>
                    {restaurant.categories && restaurant.categories.length > 0 && (
                      <p className="categories">{restaurant.categories.join(', ')}</p>
                    )}
                    {restaurant.address && <p className="address">{restaurant.address}</p>}
                  </div>
                  <button
                    onClick={() => isSelected ? handleRemoveRestaurant(restaurant.yelp_id) : handleSelectRestaurant(restaurant)}
                    className={isSelected ? 'btn-selected' : 'btn-select'}
                    disabled={!isSelected && selectedRestaurants.length >= 3}
                  >
                    {isSelected ? 'Selected ✓' : 'Select'}
                  </button>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Selected Restaurants */}
      {selectedRestaurants.length > 0 && (
        <div className="selected-restaurants">
          <h4>Your Selections ({selectedRestaurants.length}/3)</h4>
          <div className="selected-list">
            {selectedRestaurants.map((restaurant, index) => (
              <div key={restaurant.yelp_id} className="selected-badge">
                <span className="badge-number">{index + 1}</span>
                <span className="badge-name">{restaurant.name}</span>
                <button onClick={() => handleRemoveRestaurant(restaurant.yelp_id)} className="badge-remove">×</button>
              </div>
            ))}
          </div>
          {selectedRestaurants.length === 3 && (
            <button onClick={handleProceedToDetails} className="btn-primary proceed-btn">
              Continue to Details →
            </button>
          )}
        </div>
      )}
    </div>
  )

  // Render details step
  const renderDetailsStep = () => (
    <div className="onboarding-step">
      <h3>Tell us more about your favorites</h3>
      <p className="step-description">
        Help us understand why you love these restaurants (optional).
      </p>

      <div className="details-form">
        {selectedRestaurants.map((restaurant, index) => (
          <div key={restaurant.yelp_id} className="restaurant-detail-card">
            <div className="detail-header">
              <span className="detail-number">{index + 1}</span>
              <h4>{restaurant.name}</h4>
            </div>
            <div className="detail-inputs">
              <div className="input-group">
                <label>What do you love about this place?</label>
                <textarea
                  placeholder="e.g., Great atmosphere, friendly staff, amazing pasta..."
                  value={restaurantDetails[restaurant.yelp_id]?.notes || ''}
                  onChange={(e) => handleDetailChange(restaurant.yelp_id, 'notes', e.target.value)}
                  maxLength={500}
                />
              </div>
              <div className="input-group">
                <label>Favorite dish (if any)</label>
                <input
                  type="text"
                  placeholder="e.g., Margherita Pizza"
                  value={restaurantDetails[restaurant.yelp_id]?.favorite_dish || ''}
                  onChange={(e) => handleDetailChange(restaurant.yelp_id, 'favorite_dish', e.target.value)}
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="button-group">
        <button onClick={() => setStep('search')} className="btn-secondary">
          ← Back
        </button>
        <button onClick={handleSubmitOnboarding} className="btn-primary" disabled={loading}>
          {loading ? 'Processing...' : 'Analyze My Preferences'}
        </button>
      </div>
    </div>
  )

  // Render extracting step
  const renderExtractingStep = () => (
    <div className="onboarding-step extracting-step">
      <div className="extraction-animation">
        <div className="spinner"></div>
      </div>
      <h3>Analyzing Your Preferences</h3>
      <p className="step-description">
        We're learning what makes these restaurants special to you...
      </p>
      <div className="progress-bar">
        <div className="progress-bar-fill" style={{ width: `${extractionProgress}%` }}></div>
      </div>
      <p className="progress-text">{extractionStatus || 'Processing...'} - {extractionProgress}%</p>
    </div>
  )

  // Render questionnaire step
  const renderQuestionnaireStep = () => {
    if (!questionnaire || !questionnaire.questions) {
      return (
        <div className="onboarding-step">
          <h3>Almost done!</h3>
          <p>Finalizing your preferences...</p>
        </div>
      )
    }

    return (
      <div className="onboarding-step questionnaire-step">
        <h3>A few quick questions</h3>
        <p className="step-description">
          Help us fine-tune your recommendations ({questionnaire.questions.length} questions)
        </p>

        <div className="questionnaire-form">
          {questionnaire.questions.map((question, index) => (
            <div key={question.question_id} className="question-card">
              <p className="question-number">Question {index + 1}</p>
              <p className="question-text">{question.question_text}</p>

              {question.question_type === 'text' && (
                <textarea
                  value={answers[question.question_id] || ''}
                  onChange={(e) => handleAnswerChange(question.question_id, e.target.value)}
                  placeholder="Your answer..."
                />
              )}

              {question.question_type === 'single_choice' && question.options && (
                <div className="radio-group">
                  {question.options.map((option) => (
                    <div key={option.value} className="radio-option">
                      <input
                        type="radio"
                        id={`${question.question_id}-${option.value}`}
                        name={question.question_id}
                        value={option.value}
                        checked={answers[question.question_id] === option.value}
                        onChange={() => handleAnswerChange(question.question_id, option.value)}
                      />
                      <label htmlFor={`${question.question_id}-${option.value}`}>{option.label}</label>
                    </div>
                  ))}
                </div>
              )}

              {question.question_type === 'multi_choice' && question.options && (
                <div className="checkbox-group">
                  {question.options.map((option) => {
                    const currentAnswers = answers[question.question_id] || []
                    const isChecked = currentAnswers.includes(option.value)
                    return (
                      <div key={option.value} className="checkbox-option">
                        <input
                          type="checkbox"
                          id={`${question.question_id}-${option.value}`}
                          checked={isChecked}
                          onChange={() => {
                            const newAnswers = isChecked
                              ? currentAnswers.filter(v => v !== option.value)
                              : [...currentAnswers, option.value]
                            handleAnswerChange(question.question_id, newAnswers)
                          }}
                        />
                        <label htmlFor={`${question.question_id}-${option.value}`}>{option.label}</label>
                      </div>
                    )
                  })}
                </div>
              )}

              {question.question_type === 'boolean' && (
                <div className="boolean-group">
                  <button
                    className={`bool-btn ${answers[question.question_id] === true ? 'active' : ''}`}
                    onClick={() => handleAnswerChange(question.question_id, true)}
                  >
                    Yes
                  </button>
                  <button
                    className={`bool-btn ${answers[question.question_id] === false ? 'active' : ''}`}
                    onClick={() => handleAnswerChange(question.question_id, false)}
                  >
                    No
                  </button>
                </div>
              )}

              {question.question_type === 'rating' && (
                <div className="rating-group">
                  {[1, 2, 3, 4, 5].map((rating) => (
                    <button
                      key={rating}
                      className={`rating-btn ${answers[question.question_id] === rating ? 'active' : ''}`}
                      onClick={() => handleAnswerChange(question.question_id, rating)}
                    >
                      {rating}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        <button onClick={handleSubmitQuestionnaire} className="btn-primary submit-btn" disabled={loading}>
          {loading ? 'Saving...' : 'Complete Setup'}
        </button>
      </div>
    )
  }

  // Get progress percentage
  const getStepProgress = () => {
    switch (step) {
      case 'search': return 25
      case 'details': return 50
      case 'extracting': return 75
      case 'questionnaire': return 90
      default: return 0
    }
  }

  return (
    <div className="container">
      <div className="onboarding-container">
        <h2>Welcome, {currentUser?.username || 'there'}!</h2>
        <p className="onboarding-intro">Let's discover your dining preferences</p>

        <div className="progress-bar">
          <div className="progress-bar-fill" style={{ width: `${getStepProgress()}%` }}></div>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {step === 'search' && renderSearchStep()}
        {step === 'details' && renderDetailsStep()}
        {step === 'extracting' && renderExtractingStep()}
        {step === 'questionnaire' && renderQuestionnaireStep()}
      </div>
    </div>
  )
}

export default Onboarding
