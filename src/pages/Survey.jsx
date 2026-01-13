import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { savePreferences, getCurrentUser } from '../services/api'

function Survey() {
  const navigate = useNavigate()
  const currentUser = getCurrentUser()

  const [currentStep, setCurrentStep] = useState(1)
  const totalSteps = 5
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [preferences, setPreferences] = useState({
    cuisine_type: '',
    price_range: '',
    dining_style: '',
    dietary_restrictions: '',
    atmosphere: ''
  })

  const handleChange = (category, value) => {
    setPreferences({
      ...preferences,
      [category]: value
    })
  }

  const handleNext = () => {
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSubmit = async () => {
    setLoading(true)
    setError('')

    try {
      const data = await savePreferences(preferences)
      console.log('Preferences saved:', data)

      alert('Preferences saved successfully! Your profile is ready.')
      // Later: navigate to dashboard or chatbot page
      // For now, stay on the page or navigate to a success page
    } catch (err) {
      console.error('Error saving preferences:', err)
      setError(err.message || 'Failed to save preferences. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const renderStep = () => {
    switch(currentStep) {
      case 1:
        return (
          <div className="survey-section">
            <h3>What type of cuisine do you prefer?</h3>
            <div className="radio-group">
              {['Italian', 'Chinese', 'Mexican', 'Indian', 'Japanese', 'American'].map((option) => (
                <div key={option} className="radio-option">
                  <input
                    type="radio"
                    id={option}
                    name="cuisine_type"
                    value={option}
                    checked={preferences.cuisine_type === option}
                    onChange={() => handleChange('cuisine_type', option)}
                  />
                  <label htmlFor={option}>{option}</label>
                </div>
              ))}
            </div>
          </div>
        )

      case 2:
        return (
          <div className="survey-section">
            <h3>What's your preferred price range?</h3>
            <div className="radio-group">
              {[
                { value: 'budget', label: 'Budget ($)' },
                { value: 'moderate', label: 'Moderate ($$)' },
                { value: 'upscale', label: 'Upscale ($$$)' },
                { value: 'fine-dining', label: 'Fine Dining ($$$$)' }
              ].map((option) => (
                <div key={option.value} className="radio-option">
                  <input
                    type="radio"
                    id={option.value}
                    name="price_range"
                    value={option.value}
                    checked={preferences.price_range === option.value}
                    onChange={() => handleChange('price_range', option.value)}
                  />
                  <label htmlFor={option.value}>{option.label}</label>
                </div>
              ))}
            </div>
          </div>
        )

      case 3:
        return (
          <div className="survey-section">
            <h3>What's your preferred dining style?</h3>
            <div className="radio-group">
              {[
                { value: 'dine-in', label: 'Dine-in' },
                { value: 'takeout', label: 'Takeout' },
                { value: 'delivery', label: 'Delivery' },
                { value: 'no-preference', label: 'No Preference' }
              ].map((option) => (
                <div key={option.value} className="radio-option">
                  <input
                    type="radio"
                    id={option.value}
                    name="dining_style"
                    value={option.value}
                    checked={preferences.dining_style === option.value}
                    onChange={() => handleChange('dining_style', option.value)}
                  />
                  <label htmlFor={option.value}>{option.label}</label>
                </div>
              ))}
            </div>
          </div>
        )

      case 4:
        return (
          <div className="survey-section">
            <h3>Do you have any dietary restrictions?</h3>
            <div className="radio-group">
              {[
                'None',
                'Vegetarian',
                'Vegan',
                'Gluten-Free',
                'Halal',
                'Kosher'
              ].map((option) => (
                <div key={option} className="radio-option">
                  <input
                    type="radio"
                    id={option}
                    name="dietary_restrictions"
                    value={option}
                    checked={preferences.dietary_restrictions === option}
                    onChange={() => handleChange('dietary_restrictions', option)}
                  />
                  <label htmlFor={option}>{option}</label>
                </div>
              ))}
            </div>
          </div>
        )

      case 5:
        return (
          <div className="survey-section">
            <h3>What atmosphere do you prefer?</h3>
            <div className="radio-group">
              {[
                { value: 'casual', label: 'Casual & Relaxed' },
                { value: 'romantic', label: 'Romantic' },
                { value: 'family-friendly', label: 'Family-Friendly' },
                { value: 'trendy', label: 'Trendy & Modern' },
                { value: 'quiet', label: 'Quiet & Intimate' }
              ].map((option) => (
                <div key={option.value} className="radio-option">
                  <input
                    type="radio"
                    id={option.value}
                    name="atmosphere"
                    value={option.value}
                    checked={preferences.atmosphere === option.value}
                    onChange={() => handleChange('atmosphere', option.value)}
                  />
                  <label htmlFor={option.value}>{option.label}</label>
                </div>
              ))}
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <div className="container">
      <div className="survey-container">
        <h2>Tell us about your preferences, {currentUser?.username || 'there'}!</h2>

        <div className="progress-bar">
          <div
            className="progress-bar-fill"
            style={{ width: `${(currentStep / totalSteps) * 100}%` }}
          ></div>
        </div>

        <p style={{ textAlign: 'center', color: '#666', marginBottom: '30px' }}>
          Step {currentStep} of {totalSteps}
        </p>

        {error && (
          <div style={{
            padding: '12px',
            marginBottom: '20px',
            backgroundColor: '#fee',
            color: '#c33',
            borderRadius: '6px',
            fontSize: '14px'
          }}>
            {error}
          </div>
        )}

        {renderStep()}

        <div className="button-group">
          <button
            onClick={handlePrevious}
            className="btn-secondary"
            disabled={currentStep === 1 || loading}
            style={{ opacity: currentStep === 1 ? 0.5 : 1 }}
          >
            Previous
          </button>

          {currentStep < totalSteps ? (
            <button
              onClick={handleNext}
              className="btn-primary"
              style={{ width: 'auto', padding: '10px 24px' }}
              disabled={loading}
            >
              Next
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              className="btn-primary"
              style={{ width: 'auto', padding: '10px 24px' }}
              disabled={loading}
            >
              {loading ? 'Saving...' : 'Complete Profile'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default Survey
