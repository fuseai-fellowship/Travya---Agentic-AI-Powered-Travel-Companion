import { useState } from 'react';
import { createFileRoute, useNavigate } from '@tanstack/react-router';
import { FiMapPin, FiCalendar, FiDollarSign, FiUsers, FiLoader, FiCheck, FiArrowRight, FiArrowLeft } from 'react-icons/fi';
import { useTravel } from '@/contexts/TravelContext';
import ItineraryDisplay from '@/components/ItineraryDisplay';
import AgentActivityFeed from '@/components/AgentActivityFeed';
import Typewriter from '@/components/Typewriter';

export const Route = createFileRoute('/_layout/plan-trip')({
  component: PlanTripPage,
});

function PlanTripPage() {
  const { planTrip, isPlanning } = useTravel();
  const navigate = useNavigate();
  
  const [formData, setFormData] = useState({
    destination: '',
    startDate: '',
    endDate: '',
    budget: '',
    travelers: 1,
    tripType: 'leisure',
    interests: [] as string[],
    additionalNotes: '',
  });

  const [aiResponse, setAiResponse] = useState<any>(null);
  const [currentStep, setCurrentStep] = useState(1);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [sessionId, setSessionId] = useState<string>('');

  const tripTypes = [
    { value: 'leisure', label: 'Leisure', icon: '🏖️', description: 'Relaxing vacation' },
    { value: 'business', label: 'Business', icon: '💼', description: 'Work-related travel' },
    { value: 'adventure', label: 'Adventure', icon: '🏔️', description: 'Outdoor activities' },
    { value: 'cultural', label: 'Cultural', icon: '🏛️', description: 'History & arts' },
    { value: 'romantic', label: 'Romantic', icon: '💕', description: 'Couples getaway' },
    { value: 'family', label: 'Family', icon: '👨‍👩‍👧‍👦', description: 'Family-friendly' },
  ];

  const interestOptions = [
    'Food & Dining',
    'History & Culture',
    'Nature & Outdoors',
    'Nightlife',
    'Shopping',
    'Art & Museums',
    'Adventure Sports',
    'Photography',
    'Music & Entertainment',
    'Wellness & Spa',
  ];

  const validateStep = (step: number) => {
    const newErrors: Record<string, string> = {};
    
    if (step === 1) {
      if (!formData.destination.trim()) {
        newErrors.destination = 'Destination is required';
      }
      if (!formData.startDate) {
        newErrors.startDate = 'Start date is required';
      }
      if (!formData.endDate) {
        newErrors.endDate = 'End date is required';
      }
      if (formData.startDate && formData.endDate && new Date(formData.startDate) >= new Date(formData.endDate)) {
        newErrors.endDate = 'End date must be after start date';
      }
    } else if (step === 2) {
      if (!formData.budget || parseInt(formData.budget) <= 0) {
        newErrors.budget = 'Please enter a valid budget';
      }
      if (formData.travelers < 1 || formData.travelers > 20) {
        newErrors.travelers = 'Number of travelers must be between 1 and 20';
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleInterestToggle = (interest: string) => {
    setFormData(prev => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest]
    }));
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handlePrevious = () => {
    setCurrentStep(prev => prev - 1);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Prevent Enter key from submitting the form except on the submit button
    if (e.key === 'Enter') {
      const target = e.target as HTMLElement;
      // Allow Enter in textarea, but prevent form submission
      if (target.tagName === 'TEXTAREA') {
        e.stopPropagation(); // Don't let it bubble to form
        return;
      }
      // Prevent Enter on input fields from submitting
      if (target.tagName === 'INPUT' && target.getAttribute('type') !== 'submit') {
        e.preventDefault();
        console.log('Enter key blocked on input field');
      }
    }
  };

  // Helper function to trigger photo gallery generation
  const triggerPhotoGallery = async (tripId: string) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/v1/photo-gallery/generate/${tripId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        console.log('✅ Photo gallery generation triggered successfully');
      } else {
        const error = await response.json();
        console.log('⚠️ Photo gallery already exists or error:', error);
      }
    } catch (error) {
      console.error('❌ Error triggering photo gallery:', error);
    }
  };

  // Helper function to trigger map parsing
  const triggerMapParsing = async (tripId: string, response: any) => {
    try {
      const token = localStorage.getItem('access_token');
      const chatId = `trip_${tripId}_${Date.now()}`;
      
      // Get itinerary data from the response
      const itineraryData = response.itinerary?.itinerary || response.itinerary || response;
      
      const mapResponse = await fetch(`http://localhost:8000/api/v1/map-parser/parse-itinerary`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          itinerary_data: itineraryData,
          chat_id: chatId,
          trip_id: tripId
        })
      });

      if (mapResponse.ok) {
        console.log('✅ Map parsing triggered successfully');
      } else {
        console.log('⚠️ Map parsing error:', await mapResponse.text());
      }
    } catch (error) {
      console.error('❌ Error triggering map parsing:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    console.log('Form submit triggered, currentStep:', currentStep);
    
    // Only allow submission on step 3
    if (currentStep !== 3) {
      console.log('Not on step 3, ignoring submit');
      return;
    }
    
    // Validate all steps before final submission
    if (!formData.destination.trim()) {
      setErrors({ submit: 'Please enter a destination' });
      setCurrentStep(1);
      return;
    }
    
    if (!formData.startDate || !formData.endDate) {
      setErrors({ submit: 'Please enter travel dates' });
      setCurrentStep(1);
      return;
    }
    
    if (!formData.budget || parseInt(formData.budget) <= 0) {
      setErrors({ submit: 'Please enter a valid budget' });
      setCurrentStep(2);
      return;
    }
    
    if (!validateStep(currentStep)) {
      return;
    }

    console.log('Submitting trip plan with data:', formData);

    // Generate session ID for tracking agent progress
    const newSessionId = `trip_plan_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    setSessionId(newSessionId);
    console.log('📋 Session ID:', newSessionId);

    try {
      const response = await planTrip({
        destination: formData.destination,
        startDate: formData.startDate,
        endDate: formData.endDate,
        budget: parseInt(formData.budget) || 0,
        travelers: formData.travelers || 1,
        tripType: formData.tripType,
        interests: formData.interests,
        additionalNotes: formData.additionalNotes,
      });
      
      console.log('✅ Received AI response:', response);
      console.log('Response structure:', JSON.stringify(response, null, 2));
      setAiResponse(response);
      
      // Auto-trigger photo gallery and map parsing after trip is created
      if (response.trip_id) {
        console.log('🎯 Auto-triggering photo gallery and map parsing for trip:', response.trip_id);
        
        // Generate photo gallery in background
        triggerPhotoGallery(response.trip_id);
        
        // Parse map data in background  
        triggerMapParsing(response.trip_id, response);
      }
    } catch (error) {
      console.error('Failed to plan trip:', error);
      setErrors({ submit: 'Failed to generate trip plan. Please try again.' });
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="step-content">
            <div className="step-header">
              <h2>Where do you want to go?</h2>
              <p>Tell us your destination and travel dates</p>
            </div>
            
            <div className="form-group">
              <label htmlFor="destination" className="label-with-icon">
                <FiMapPin className="label-icon" />
                Destination *
              </label>
              <input
                id="destination"
                name="destination"
                type="text"
                placeholder="Enter city, country, or region"
                value={formData.destination}
                onChange={(e) => handleInputChange('destination', e.target.value)}
                className={errors.destination ? 'error' : ''}
                required
                aria-describedby={errors.destination ? 'destination-error' : undefined}
              />
              {errors.destination && (
                <div id="destination-error" className="error-message">
                  {errors.destination}
                </div>
              )}
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="startDate" className="label-with-icon">
                  <FiCalendar className="label-icon" />
                  Start Date *
                </label>
                <input
                  id="startDate"
                  name="startDate"
                  type="date"
                  value={formData.startDate}
                  onChange={(e) => handleInputChange('startDate', e.target.value)}
                  className={errors.startDate ? 'error' : ''}
                  required
                  aria-describedby={errors.startDate ? 'startDate-error' : undefined}
                />
                {errors.startDate && (
                  <div id="startDate-error" className="error-message">
                    {errors.startDate}
                  </div>
                )}
              </div>
              <div className="form-group">
                <label htmlFor="endDate" className="label-with-icon">
                  <FiCalendar className="label-icon" />
                  End Date *
                </label>
                <input
                  id="endDate"
                  name="endDate"
                  type="date"
                  value={formData.endDate}
                  onChange={(e) => handleInputChange('endDate', e.target.value)}
                  className={errors.endDate ? 'error' : ''}
                  required
                  aria-describedby={errors.endDate ? 'endDate-error' : undefined}
                />
                {errors.endDate && (
                  <div id="endDate-error" className="error-message">
                    {errors.endDate}
                  </div>
                )}
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="step-content">
            <div className="step-header">
              <h2>Tell us about your trip</h2>
              <p>Choose your trip type and travel details</p>
            </div>
            
            <div className="form-group">
              <fieldset>
                <legend>Trip Type *</legend>
                <div className="trip-type-grid">
                  {tripTypes.map((type) => (
                    <label key={type.value} className="trip-type-card">
                      <input
                        type="radio"
                        name="tripType"
                        value={type.value}
                        checked={formData.tripType === type.value}
                        onChange={(e) => handleInputChange('tripType', e.target.value)}
                        className="sr-only"
                      />
                      <div className={`trip-type-content ${formData.tripType === type.value ? 'selected' : ''}`}>
                        <span className="trip-type-icon">{type.icon}</span>
                        <div className="trip-type-info">
                          <span className="trip-type-label">{type.label}</span>
                          <span className="trip-type-description">{type.description}</span>
                        </div>
                        {formData.tripType === type.value && (
                          <FiCheck className="trip-type-check" />
                        )}
                      </div>
                    </label>
                  ))}
                </div>
              </fieldset>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="travelers" className="label-with-icon">
                  <FiUsers className="label-icon" />
                  Number of Travelers *
                </label>
                <input
                  id="travelers"
                  name="travelers"
                  type="number"
                  min="1"
                  max="20"
                  value={formData.travelers}
                  onChange={(e) => {
                    const value = e.target.value === '' ? 1 : parseInt(e.target.value) || 1;
                    handleInputChange('travelers', value);
                  }}
                  className={errors.travelers ? 'error' : ''}
                  required
                  aria-describedby={errors.travelers ? 'travelers-error' : undefined}
                />
                {errors.travelers && (
                  <div id="travelers-error" className="error-message">
                    {errors.travelers}
                  </div>
                )}
              </div>
              <div className="form-group">
                <label htmlFor="budget" className="label-with-icon">
                  <FiDollarSign className="label-icon" />
                  Budget (USD) *
                </label>
                <input
                  id="budget"
                  name="budget"
                  type="number"
                  min="0"
                  step="1"
                  placeholder="Enter your budget"
                  value={formData.budget}
                  onChange={(e) => handleInputChange('budget', e.target.value)}
                  className={errors.budget ? 'error' : ''}
                  required
                  aria-describedby={errors.budget ? 'budget-error' : undefined}
                />
                {errors.budget && (
                  <div id="budget-error" className="error-message">
                    {errors.budget}
                  </div>
                )}
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="step-content">
            <div className="step-header">
              <h2>What interests you?</h2>
              <p>Help us personalize your experience (optional)</p>
            </div>
            
            <div className="form-group">
              <fieldset>
                <legend>Select your interests</legend>
                <div className="interests-grid">
                  {interestOptions.map((interest) => (
                    <label key={interest} className="interest-chip">
                      <input
                        type="checkbox"
                        name="interests"
                        value={interest}
                        checked={formData.interests.includes(interest)}
                        onChange={() => handleInterestToggle(interest)}
                        className="sr-only"
                      />
                      <div className={`interest-content ${formData.interests.includes(interest) ? 'selected' : ''}`}>
                        {interest}
                        {formData.interests.includes(interest) && (
                          <FiCheck className="interest-check" />
                        )}
                      </div>
                    </label>
                  ))}
                </div>
              </fieldset>
            </div>

            <div className="form-group">
              <label htmlFor="additionalNotes">Additional Notes</label>
              <textarea
                id="additionalNotes"
                name="additionalNotes"
                placeholder="Any specific requirements, preferences, or special requests?"
                value={formData.additionalNotes}
                onChange={(e) => handleInputChange('additionalNotes', e.target.value)}
                rows={4}
                aria-describedby="additionalNotes-help"
              />
              <div id="additionalNotes-help" className="help-text">
                Optional: Tell us about any special requirements or preferences
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  if (aiResponse) {
    return (
      <div className="plan-trip-page">
        <div className="page-header">
          <h1>Your AI-Generated Trip Plan</h1>
          <p>Here's your personalized itinerary for {formData.destination}</p>
        </div>

        <div className="ai-response">
          <div className="response-header">
            <div className="ai-avatar">
              <FiMapPin />
            </div>
            <div>
              <h3>AI Travel Assistant</h3>
              <p>Generated your personalized trip plan</p>
            </div>
          </div>

          <div className="response-content">
            {aiResponse.itinerary ? (
              <ItineraryDisplay itinerary={aiResponse.itinerary} />
            ) : (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
                <p className="text-yellow-800">
                  Your trip is being planned! The AI agents are working on creating your personalized itinerary.
                </p>
                {aiResponse.trip_summary && (
                  <div className="mt-4">
                    <h4 className="font-semibold mb-2">Summary:</h4>
                    <p className="text-gray-700">{aiResponse.trip_summary.summary}</p>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="response-actions">
            <button 
              className="btn btn-outline"
              onClick={() => {
                setAiResponse(null);
                setCurrentStep(1);
                setErrors({});
              }}
            >
              Plan Another Trip
            </button>
            <button 
              className="btn btn-primary"
              onClick={() => navigate({ to: '/trips' })}
            >
              Save to My Trips
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="plan-trip-page">
      <div className="page-header">
        <h1>
          <Typewriter 
            text="Create Your Perfect Travel Itinerary" 
            speed={80} 
            loop={true}
            loopDelay={3000}
          />
        </h1>
      </div>

      {/* Agent Activity Feed - Show during planning */}
      {isPlanning && sessionId && (
        <div className="mb-6">
          <AgentActivityFeed 
            sessionId={sessionId}
            isActive={isPlanning}
          />
        </div>
      )}

      <div className="planning-wizard">
        <div className="wizard-progress">
          {[1, 2, 3].map((step) => (
            <div key={step} className={`progress-step ${currentStep >= step ? 'active' : ''} ${currentStep > step ? 'completed' : ''}`}>
              <div className="step-number">
                {currentStep > step ? <FiCheck /> : step}
              </div>
              <div className="step-label">
                {step === 1 && 'Destination & Dates'}
                {step === 2 && 'Trip Details'}
                {step === 3 && 'Preferences'}
              </div>
            </div>
          ))}
        </div>

        <form onSubmit={handleSubmit} onKeyDown={handleKeyDown} className="planning-form">
          {renderStep()}

          {errors.submit && (
            <div className="error-message submit-error">
              {errors.submit}
            </div>
          )}

          <div className="form-actions">
            {currentStep > 1 && (
              <button
                type="button"
                className="btn btn-outline"
                onClick={handlePrevious}
              >
                <FiArrowLeft className="icon" />
                Previous
              </button>
            )}
            {currentStep < 3 ? (
              <button
                type="button"
                className="btn btn-primary"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  console.log('Next button clicked, advancing from step', currentStep);
                  handleNext();
                }}
              >
                Next
                <FiArrowRight className="icon" />
              </button>
            ) : (
              <button
                type="submit"
                className="btn btn-primary"
                disabled={isPlanning}
                onClick={() => {
                  console.log('Generate Trip Plan button clicked');
                }}
              >
                {isPlanning ? (
                  <>
                    <FiLoader className="icon spinning" />
                    Planning...
                  </>
                ) : (
                  <>
                    <FiMapPin className="icon" />
                    Generate Trip Plan
                  </>
                )}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}