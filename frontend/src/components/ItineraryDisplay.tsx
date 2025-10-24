import { motion } from 'framer-motion';
import { 
  FiClock, 
  FiMapPin, 
  FiDollarSign, 
  FiCalendar,
  FiCoffee,
  FiSun,
  FiMoon,
  FiNavigation,
  FiInfo
} from 'react-icons/fi';

interface Activity {
  time: string;
  activity: string;
  location: string;
  duration: string;
  cost: number;
  description: string;
  tips: string;
}

interface Meal {
  time: string;
  type: string;
  restaurant: string;
  cuisine: string;
  cost: number;
  reservation_required: boolean;
}

interface Transportation {
  from: string;
  to: string;
  method: string;
  duration: string;
  cost: number;
  tips: string;
}

interface DayItinerary {
  day: number;
  date: string;
  theme: string;
  activities: Activity[];
  meals: Meal[];
  transportation: Transportation[];
  daily_budget: number;
  daily_tips: string;
}

interface Overview {
  destination: string;
  duration: number;
  total_estimated_cost: number;
  difficulty_level: string;
  best_time_to_visit: string;
}

interface ItineraryData {
  overview: Overview;
  days: DayItinerary[];
}

interface Props {
  itinerary: any;
}

export default function ItineraryDisplay({ itinerary }: Props) {
  // Extract the nested itinerary data
  const itineraryData: ItineraryData | null = 
    itinerary?.itinerary?.itinerary ||
    itinerary?.itinerary ||
    // Fallback: support when we already pass the inner itinerary object
    (itinerary && itinerary.overview && itinerary.days ? (itinerary as ItineraryData) : null);

  if (!itineraryData || !itineraryData.overview) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
        <p className="text-yellow-800">No itinerary data available yet.</p>
      </div>
    );
  }

  const { overview, days } = itineraryData;

  return (
    <div className="space-y-6">
      {/* Overview Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl p-6 text-white shadow-lg"
      >
        <h2 className="text-3xl font-bold mb-4">{overview.destination}</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <FiCalendar className="inline mr-2" />
            <span className="font-semibold">{overview.duration} Days</span>
          </div>
          <div>
            <FiDollarSign className="inline mr-2" />
            <span className="font-semibold">${overview.total_estimated_cost}</span>
          </div>
          <div>
            <FiInfo className="inline mr-2" />
            <span className="font-semibold">{overview.difficulty_level}</span>
          </div>
          <div className="col-span-2 md:col-span-1">
            <FiSun className="inline mr-2" />
            <span className="text-sm">{overview.best_time_to_visit}</span>
          </div>
        </div>
      </motion.div>

      {/* Daily Itineraries */}
      {days && days.map((day, dayIndex) => (
        <motion.div
          key={day.day}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: dayIndex * 0.1 }}
          className="bg-white rounded-xl shadow-md overflow-hidden border border-gray-200"
        >
          {/* Day Header */}
          <div className="bg-gradient-to-r from-indigo-500 to-blue-500 text-white p-4">
            <h3 className="text-2xl font-bold">Day {day.day}: {day.theme}</h3>
            <p className="text-sm opacity-90">{day.date}</p>
            <div className="mt-2 flex items-center gap-4">
              <span className="bg-white/20 px-3 py-1 rounded-full text-sm">
                <FiDollarSign className="inline mr-1" />
                Budget: ${day.daily_budget}
              </span>
            </div>
          </div>

          <div className="p-6 space-y-6">
            {/* Activities */}
            {day.activities && day.activities.length > 0 && (
              <div>
                <h4 className="text-lg font-semibold mb-3 flex items-center">
                  <FiMapPin className="mr-2 text-indigo-600" />
                  Activities
                </h4>
                <div className="space-y-4">
                  {day.activities.map((activity, idx) => (
                    <div key={idx} className="border-l-4 border-indigo-400 pl-4 py-2">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <p className="font-semibold text-gray-900">{activity.activity}</p>
                          <p className="text-sm text-gray-600 flex items-center mt-1">
                            <FiClock className="mr-1" size={14} />
                            {activity.time} • {activity.duration}
                          </p>
                        </div>
                        {activity.cost > 0 && (
                          <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-sm font-semibold">
                            ${activity.cost}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mb-1">
                        <FiMapPin className="inline mr-1" size={12} />
                        {activity.location}
                      </p>
                      <p className="text-sm text-gray-700">{activity.description}</p>
                      {activity.tips && (
                        <p className="text-sm text-blue-600 mt-1 italic">
                          💡 {activity.tips}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Meals */}
            {day.meals && day.meals.length > 0 && (
              <div>
                <h4 className="text-lg font-semibold mb-3 flex items-center">
                  <FiCoffee className="mr-2 text-orange-600" />
                  Meals
                </h4>
                <div className="grid md:grid-cols-3 gap-4">
                  {day.meals.map((meal, idx) => (
                    <div key={idx} className="bg-orange-50 rounded-lg p-3 border border-orange-200">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-gray-900">
                          {meal.type === 'Breakfast' && <FiSun className="inline mr-1 text-yellow-500" />}
                          {meal.type === 'Lunch' && <FiCoffee className="inline mr-1 text-orange-500" />}
                          {meal.type === 'Dinner' && <FiMoon className="inline mr-1 text-indigo-500" />}
                          {meal.type}
                        </span>
                        <span className="text-sm font-semibold text-green-700">${meal.cost}</span>
                      </div>
                      <p className="text-sm text-gray-700 font-medium">{meal.restaurant}</p>
                      <p className="text-xs text-gray-600">{meal.cuisine}</p>
                      <p className="text-xs text-gray-500 mt-1">{meal.time}</p>
                      {meal.reservation_required && (
                        <p className="text-xs text-red-600 mt-1">⚠️ Reservation required</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Transportation */}
            {day.transportation && day.transportation.length > 0 && (
              <div>
                <h4 className="text-lg font-semibold mb-3 flex items-center">
                  <FiNavigation className="mr-2 text-blue-600" />
                  Transportation
                </h4>
                <div className="space-y-2">
                  {day.transportation.map((transport, idx) => (
                    <div key={idx} className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="text-sm font-semibold text-gray-900">
                            {transport.from} → {transport.to}
                          </p>
                          <p className="text-xs text-gray-600">
                            {transport.method} • {transport.duration}
                          </p>
                          {transport.tips && (
                            <p className="text-xs text-blue-600 mt-1 italic">💡 {transport.tips}</p>
                          )}
                        </div>
                        <span className="text-sm font-semibold text-green-700">${transport.cost}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Daily Tips */}
            {day.daily_tips && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h4 className="font-semibold text-yellow-900 mb-2">💡 Daily Tips</h4>
                <p className="text-sm text-yellow-800">{day.daily_tips}</p>
              </div>
            )}
          </div>
        </motion.div>
      ))}

      {/* Enhancements Section (if available) */}
      {itinerary?.enhancements && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-xl shadow-md p-6 border border-gray-200"
        >
          <h3 className="text-xl font-bold mb-4">Trip Essentials</h3>
          
          <div className="grid md:grid-cols-2 gap-6">
            {/* Packing List */}
            {itinerary.enhancements.packing_list && (
              <div>
                <h4 className="font-semibold mb-2">📦 Packing List</h4>
                <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                  {itinerary.enhancements.packing_list.map((item: string, idx: number) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Safety Tips */}
            {itinerary.enhancements.safety_tips && (
              <div>
                <h4 className="font-semibold mb-2">🛡️ Safety Tips</h4>
                <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                  {itinerary.enhancements.safety_tips.map((tip: string, idx: number) => (
                    <li key={idx}>{tip}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Local Customs */}
            {itinerary.enhancements.local_customs && (
              <div>
                <h4 className="font-semibold mb-2">🌍 Local Customs</h4>
                <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                  {itinerary.enhancements.local_customs.map((custom: string, idx: number) => (
                    <li key={idx}>{custom}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Weather Preparation */}
            {itinerary.enhancements.weather_preparation && (
              <div>
                <h4 className="font-semibold mb-2">🌤️ Weather Preparation</h4>
                <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                  {itinerary.enhancements.weather_preparation.map((item: string, idx: number) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Emergency Contacts */}
          {itinerary.enhancements.emergency_contacts && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
              <h4 className="font-semibold text-red-900 mb-2">🚨 Emergency Contacts</h4>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
                {Object.entries(itinerary.enhancements.emergency_contacts).map(([key, value]) => (
                  <div key={key}>
                    <span className="font-medium capitalize">{key.replace('_', ' ')}: </span>
                    <span className="text-gray-700">{value as string}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}

