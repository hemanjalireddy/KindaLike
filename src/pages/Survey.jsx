import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

function Survey() {
  const navigate = useNavigate()
  const username = localStorage.getItem('username')

  const [currentStep, setCurrentStep] = useState(1)
  const totalSteps = 5

  const [preferences, setPreferences] = useState({
    cuisineType: '',
    priceRange: '',
    diningStyle: '',
    dietaryRestrictions: '',
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

  const handleSubmit = () => {
    // TODO: Save preferences to database
    console.log('User preferences:', {
      username: username,
      ...preferences
    })

    alert('Preferences saved! Your profile is ready.')
    // Later: navigate to dashboard or chatbot page
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
                    name="cuisineType"
                    value={option}
                    checked={preferences.cuisineType === option}
                    onChange={() => handleChange('cuisineType', option)}
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
                    name="priceRange"
                    value={option.value}
                    checked={preferences.priceRange === option.value}
                    onChange={() => handleChange('priceRange', option.value)}
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
                    name="diningStyle"
                    value={option.value}
                    checked={preferences.diningStyle === option.value}
                    onChange={() => handleChange('diningStyle', option.value)}
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
                    name="dietaryRestrictions"
                    value={option}
                    checked={preferences.dietaryRestrictions === option}
                    onChange={() => handleChange('dietaryRestrictions', option)}
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
        <h2>Tell us about your preferences, {username}!</h2>

        <div className="progress-bar">
          <div
            className="progress-bar-fill"
            style={{ width: `${(currentStep / totalSteps) * 100}%` }}
          ></div>
        </div>

        <p style={{ textAlign: 'center', color: '#666', marginBottom: '30px' }}>
          Step {currentStep} of {totalSteps}
        </p>

        {renderStep()}

        <div className="button-group">
          <button
            onClick={handlePrevious}
            className="btn-secondary"
            disabled={currentStep === 1}
            style={{ opacity: currentStep === 1 ? 0.5 : 1 }}
          >
            Previous
          </button>

          {currentStep < totalSteps ? (
            <button onClick={handleNext} className="btn-primary" style={{ width: 'auto', padding: '10px 24px' }}>
              Next
            </button>
          ) : (
            <button onClick={handleSubmit} className="btn-primary" style={{ width: 'auto', padding: '10px 24px' }}>
              Complete Profile
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default Survey
