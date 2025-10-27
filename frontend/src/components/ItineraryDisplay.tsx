import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FiClock, 
  FiMapPin,
  FiCoffee,
  FiSun,
  FiMoon,
  FiInfo,
  FiChevronDown,
  FiChevronUp,
  FiDownload,
  FiShare2,
  FiCopy
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
  const [expandedDays, setExpandedDays] = useState<Set<number>>(new Set([1]));
  const [copiedToClipboard, setCopiedToClipboard] = useState(false);

  // Extract the nested itinerary data
  const itineraryData: ItineraryData | null = 
    itinerary?.itinerary?.itinerary ||
    itinerary?.itinerary ||
    (itinerary && itinerary.overview && itinerary.days ? (itinerary as ItineraryData) : null);

  if (!itineraryData || !itineraryData.overview) {
    return (
      <div className="rounded-2xl p-12 text-center bg-gray-900/50 border border-gray-800">
        <p className="text-gray-400">No itinerary data available yet.</p>
      </div>
    );
  }

  const { overview, days } = itineraryData;

  const toggleDay = (day: number) => {
    const newExpanded = new Set(expandedDays);
    if (newExpanded.has(day)) {
      newExpanded.delete(day);
    } else {
      newExpanded.add(day);
    }
    setExpandedDays(newExpanded);
  };

  const downloadItinerary = () => {
    const text = `Itinerary for ${overview.destination}\n${'='.repeat(50)}\n\n${days.map(day => 
      `Day ${day.day}: ${day.theme}\nDate: ${day.date}\nBudget: $${day.daily_budget}\n\n` +
      day.activities.map(a => `  • ${a.time} - ${a.activity} (${a.duration}) at ${a.location}`).join('\n')
    ).join('\n\n')}`;
    
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${overview.destination.replace(/\s+/g, '_')}_itinerary.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = async () => {
    const text = `Check out my trip to ${overview.destination}! ${window.location.href}`;
    await navigator.clipboard.writeText(text);
    setCopiedToClipboard(true);
    setTimeout(() => setCopiedToClipboard(false), 2000);
  };

  const scrollToDay = (day: number) => {
    const element = document.getElementById(`day-${day}`);
    element?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="space-y-4">
      {/* Apple-style Overview Header */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
        className="rounded-2xl p-8 bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700/50 backdrop-blur-xl"
      >
        <div className="flex justify-between items-start mb-6">
          <div>
            <h2 className="text-4xl font-light tracking-tight text-white mb-2">{overview.destination}</h2>
            <p className="text-slate-400 text-sm font-light">{overview.duration} days</p>
          </div>
          <div className="flex gap-1.5">
            <button
              onClick={copyToClipboard}
              className="p-2.5 hover:bg-white/10 rounded-full transition-all duration-200"
              title="Copy trip link"
            >
              {copiedToClipboard ? <FiCopy className="text-green-400" /> : <FiShare2 className="text-slate-300" />}
            </button>
            <button
              onClick={downloadItinerary}
              className="p-2.5 hover:bg-white/10 rounded-full transition-all duration-200"
              title="Download itinerary"
            >
              <FiDownload className="text-slate-300" />
            </button>
          </div>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <div className="text-slate-400 text-xs font-medium mb-1.5 uppercase tracking-wide">Duration</div>
            <div className="text-white text-lg font-light">{overview.duration} Days</div>
          </div>
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <div className="text-slate-400 text-xs font-medium mb-1.5 uppercase tracking-wide">Budget</div>
            <div className="text-white text-lg font-light">${overview.total_estimated_cost}</div>
          </div>
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <div className="text-slate-400 text-xs font-medium mb-1.5 uppercase tracking-wide">Intensity</div>
            <div className="text-white text-lg font-light">{overview.difficulty_level}</div>
          </div>
          <div className="p-4 rounded-xl bg-white/5 border border-white/10">
            <div className="text-slate-400 text-xs font-medium mb-1.5 uppercase tracking-wide">Best Time</div>
            <div className="text-white text-sm font-light">{overview.best_time_to_visit}</div>
          </div>
        </div>
      </motion.div>

      {/* Minimalist Quick Navigation */}
      {days.length > 1 && (
        <div className="flex gap-1.5 justify-center">
          {days.map(day => (
            <button
              key={day.day}
              onClick={() => scrollToDay(day.day)}
              className="px-4 py-2 text-sm font-light text-slate-400 hover:text-white hover:bg-white/5 rounded-full transition-all duration-200"
            >
              Day {day.day}
            </button>
          ))}
        </div>
      )}

      {/* Apple-style Daily Cards */}
      {days && days.map((day, dayIndex) => {
        const isExpanded = expandedDays.has(day.day);
        const dayTotalActivities = (day.activities?.length || 0) + (day.meals?.length || 0) + (day.transportation?.length || 0);
        
        return (
          <motion.div
            key={day.day}
            id={`day-${day.day}`}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: dayIndex * 0.05, duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
            className="rounded-2xl bg-gray-900/50 border border-gray-800 overflow-hidden backdrop-blur-xl"
          >
            {/* Elegant Day Header */}
            <button
              onClick={() => toggleDay(day.day)}
              className="w-full p-6 hover:bg-gray-800/50 transition-all duration-200 text-left"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1.5">
                    <span className="text-slate-500 text-sm font-light">Day {day.day}</span>
                    <span className="text-slate-600">•</span>
                    <span className="text-white text-lg font-light">{day.theme}</span>
                  </div>
                  <div className="flex items-center gap-4 text-xs text-slate-500">
                    <span>{day.date}</span>
                    <span className="text-slate-600">•</span>
                    <span>${day.daily_budget} budget</span>
                    <span className="text-slate-600">•</span>
                    <span>{dayTotalActivities} items</span>
                  </div>
                </div>
                <div className="ml-4 text-slate-500">
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={isExpanded ? 'up' : 'down'}
                      initial={{ rotate: -90 }}
                      animate={{ rotate: 0 }}
                      exit={{ rotate: 90 }}
                      transition={{ duration: 0.2 }}
                    >
                      {isExpanded ? <FiChevronUp size={20} /> : <FiChevronDown size={20} />}
                    </motion.div>
                  </AnimatePresence>
                </div>
              </div>
            </button>

            <AnimatePresence>
              {isExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                  className="overflow-hidden"
                >
                  <div className="p-6 pt-0 space-y-6">
                    {/* Activities */}
                    {day.activities && day.activities.length > 0 && (
                      <SimpleSection
                        title="Activities"
                        items={day.activities.map((activity, idx) => (
                          <div key={idx} className="py-4 border-b border-gray-800 last:border-0">
                            <div className="flex items-start justify-between gap-4 mb-2">
                              <h4 className="text-white font-medium text-base flex-1">{activity.activity}</h4>
                              {activity.cost > 0 && (
                                <span className="text-green-400 text-sm font-light whitespace-nowrap">${activity.cost}</span>
                              )}
                            </div>
                            <div className="space-y-1.5 text-sm">
                              <div className="flex items-center gap-2 text-slate-400">
                                <FiClock size={14} />
                                <span>{activity.time} • {activity.duration}</span>
                              </div>
                              <div className="flex items-center gap-2 text-slate-400">
                                <FiMapPin size={14} />
                                <a 
                                  href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(activity.location)}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-blue-400 hover:text-blue-300 transition-colors"
                                >
                                  {activity.location}
                                </a>
                              </div>
                            </div>
                            {activity.description && (
                              <p className="text-slate-300 text-sm font-light mt-3 leading-relaxed">{activity.description}</p>
                            )}
                            {activity.tips && (
                              <div className="mt-3 p-3 rounded-lg bg-blue-950/30 border border-blue-900/20">
                                <p className="text-blue-300 text-xs font-light leading-relaxed">
                                  <FiInfo className="inline mr-1.5" size={12} />
                                  {activity.tips}
                                </p>
                              </div>
                            )}
                          </div>
                        ))}
                      />
                    )}

                    {/* Meals */}
                    {day.meals && day.meals.length > 0 && (
                      <SimpleSection
                        title="Meals"
                        items={day.meals.map((meal, idx) => (
                          <div key={idx} className="py-3 px-4 rounded-xl bg-gray-800/30 border border-gray-800/50">
                            <div className="flex items-center justify-between mb-1.5">
                              <span className="text-white font-medium flex items-center gap-2">
                                {meal.type === 'Breakfast' && <FiSun className="text-yellow-400" size={16} />}
                                {meal.type === 'Lunch' && <FiCoffee className="text-orange-400" size={16} />}
                                {meal.type === 'Dinner' && <FiMoon className="text-indigo-400" size={16} />}
                                {meal.type}
                              </span>
                              <span className="text-green-400 text-sm font-light">${meal.cost}</span>
                            </div>
                            <p className="text-slate-300 text-sm font-light">{meal.restaurant}</p>
                            <p className="text-slate-500 text-xs font-light">{meal.cuisine}</p>
                            {meal.reservation_required && (
                              <p className="text-amber-400 text-xs font-light mt-2">Reservation required</p>
                            )}
                          </div>
                        ))}
                      />
                    )}

                    {/* Transportation */}
                    {day.transportation && day.transportation.length > 0 && (
                      <SimpleSection
                        title="Transportation"
                        items={day.transportation.map((transport, idx) => (
                          <div key={idx} className="py-3 px-4 rounded-xl bg-gray-800/30 border border-gray-800/50">
                            <div className="flex items-center justify-between">
                              <div className="flex-1">
                                <p className="text-white text-sm font-medium">
                                  {transport.from} → {transport.to}
                                </p>
                                <p className="text-slate-500 text-xs font-light mt-0.5">
                                  {transport.method} • {transport.duration}
                                </p>
                              </div>
                              <span className="text-green-400 text-sm font-light whitespace-nowrap">${transport.cost}</span>
                            </div>
                          </div>
                        ))}
                      />
                    )}

                    {/* Daily Tips */}
                    {day.daily_tips && (
                      <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-900/20">
                        <p className="text-amber-200 text-sm font-light leading-relaxed">
                          {day.daily_tips}
                        </p>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        );
      })}
    </div>
  );
}

// Minimalist Section Component
function SimpleSection({ title, items }: { title: string; items: JSX.Element[] }) {
  const [isExpanded, setIsExpanded] = useState(true);
  
  return (
    <div>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full mb-4 text-left group"
      >
        <span className="text-slate-400 text-xs font-medium uppercase tracking-wider">{title}</span>
        <span className="text-slate-600 text-xs">({items.length})</span>
      </button>
      {isExpanded && (
        <div className="space-y-2">
          {items}
        </div>
      )}
    </div>
  );
}
