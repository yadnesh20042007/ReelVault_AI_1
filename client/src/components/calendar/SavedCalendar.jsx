/* eslint-disable react-refresh/only-export-components */
import { useMemo, useState } from 'react';
import { CalendarDays, ChevronLeft, ChevronRight, X } from 'lucide-react';

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export function dateKey(value) {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
}

export function formatReadableDate(keyOrDate) {
  if (!keyOrDate) return '';
  let date;
  if (typeof keyOrDate === 'string' && keyOrDate.includes('-')) {
    const [y, m, d] = keyOrDate.split('-').map(Number);
    date = new Date(y, m, d);
  } else {
    date = new Date(keyOrDate);
  }
  if (Number.isNaN(date.getTime())) return '';
  return new Intl.DateTimeFormat(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(date);
}

export default function SavedCalendar({
  reels = [],
  importantDates = [],
  selectedKey = '',
  onSelect,
  onViewOpportunity,
  className = '',
}) {
  const [currentMonth, setCurrentMonth] = useState(() => {
    return new Date(new Date().getFullYear(), new Date().getMonth(), 1);
  });
  const [hoveredKey, setHoveredKey] = useState(null);

  // Group events by day, attaching reel info
  const eventsByDay = useMemo(() => {
    const map = new Map();
    importantDates.forEach((event) => {
      const key = dateKey(`${event.event_date}T00:00:00`);
      if (!key) return;
      if (!map.has(key)) map.set(key, []);
      
      const reel = reels?.find(r => r.reel_id === event.reel_id);
      map.get(key).push({
        id: event.id,
        label: event.label,
        reel
      });
    });
    return map;
  }, [importantDates, reels]);

  const year = currentMonth.getFullYear();
  const monthIndex = currentMonth.getMonth();

  const monthLabel = new Intl.DateTimeFormat(undefined, {
    month: 'long',
    year: 'numeric',
  }).format(currentMonth);

  const firstWeekday = new Date(year, monthIndex, 1).getDay();
  const daysInMonth = new Date(year, monthIndex + 1, 0).getDate();
  const daysInPrevMonth = new Date(year, monthIndex, 0).getDate();

  const todayKey = dateKey(new Date());

  // Build grid: previous month padding + current month days + next month padding
  const cells = useMemo(() => {
    const result = [];
    // Prev month padding
    for (let i = firstWeekday - 1; i >= 0; i--) {
      result.push({
        day: daysInPrevMonth - i,
        isCurrentMonth: false,
        key: null,
      });
    }
    // Current month days
    for (let day = 1; day <= daysInMonth; day++) {
      result.push({
        day,
        isCurrentMonth: true,
        key: `${year}-${monthIndex}-${day}`,
      });
    }
    // Next month padding to fill row or minimum 35 cells
    const targetLength = result.length <= 35 ? 35 : 42;
    let nextDay = 1;
    while (result.length < targetLength) {
      result.push({
        day: nextDay++,
        isCurrentMonth: false,
        key: null,
      });
    }
    return result;
  }, [year, monthIndex, firstWeekday, daysInMonth, daysInPrevMonth]);

  const goToPrevMonth = () => setCurrentMonth(new Date(year, monthIndex - 1, 1));
  const goToNextMonth = () => setCurrentMonth(new Date(year, monthIndex + 1, 1));
  const goToToday = () => {
    const now = new Date();
    setCurrentMonth(new Date(now.getFullYear(), now.getMonth(), 1));
    if (onSelect) onSelect(todayKey);
  };

  const displayKey = hoveredKey || selectedKey;
  const displayEvents = eventsByDay.get(displayKey) || [];

  return (
    <div className={`grid grid-cols-1 lg:grid-cols-[400px_1fr] gap-6 items-start ${className}`}>
      {/* Calendar Section */}
      <section
        className="bg-white rounded-[1.75rem] p-5 sm:p-6 border border-[#E3D4F8] shadow-sm transition-all"
        aria-label="Saved reels calendar"
      >
        {/* Header Bar */}
        <div className="flex items-center justify-between gap-2 mb-4">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[#F0E8FF] text-[#6D28D9] flex items-center justify-center">
              <CalendarDays size={16} />
            </div>
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-[#6D28D9]">
                Vault Calendar
              </h3>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={goToToday}
              className="text-[10px] font-bold uppercase tracking-wider text-[#6D28D9] bg-[#F0E8FF] hover:bg-[#E3D4F8] px-2.5 py-1 rounded-lg transition-colors cursor-pointer"
              title="Jump to current month"
            >
              Today
            </button>
            <button type="button" onClick={goToPrevMonth} className="p-1.5 rounded-lg text-[#776A83] hover:text-[#6D28D9] hover:bg-[#F0E8FF] transition-colors cursor-pointer">
              <ChevronLeft size={16} />
            </button>
            <button type="button" onClick={goToNextMonth} className="p-1.5 rounded-lg text-[#776A83] hover:text-[#6D28D9] hover:bg-[#F0E8FF] transition-colors cursor-pointer">
              <ChevronRight size={16} />
            </button>
          </div>
        </div>

        {/* Month & Year Title */}
        <div className="flex items-center justify-between mb-3 px-1">
          <span className="font-display text-base sm:text-lg tracking-wide uppercase text-[#261B33]">
            {monthLabel}
          </span>
          {selectedKey && onSelect && (
            <button
              type="button"
              onClick={() => onSelect('')}
              className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#776A83] hover:text-red-500 transition-colors cursor-pointer"
            >
              <X size={12} />
              <span>Reset filter</span>
            </button>
          )}
        </div>

        {/* Weekday Labels */}
        <div className="grid grid-cols-7 text-center mb-2">
          {WEEKDAYS.map((day) => (
            <span key={day} className="text-[11px] font-bold uppercase tracking-wider text-[#776A83]/70 pb-1">
              {day.slice(0, 3)}
            </span>
          ))}
        </div>

        {/* Days Grid */}
        <div className="grid grid-cols-7 text-center gap-1">
          {cells.map((cell, idx) => {
            if (!cell.isCurrentMonth) {
              return (
                <div key={`pad-${idx}`} className="mx-auto flex h-8 w-8 sm:h-9 sm:w-9 items-center justify-center text-xs text-[#776A83]/30 font-medium select-none">
                  {cell.day}
                </div>
              );
            }

            const dayEvents = eventsByDay.get(cell.key) || [];
            const count = dayEvents.length;
            const isSelected = selectedKey === cell.key;
            const isToday = todayKey === cell.key;

            return (
              <div 
                key={cell.key} 
                className="relative mx-auto"
                onMouseEnter={() => {
                  if (count > 0) setHoveredKey(cell.key);
                }}
                onMouseLeave={() => {
                  setHoveredKey(null);
                }}
              >
                <button
                  type="button"
                  onClick={() => {
                    if (onSelect) {
                      onSelect(isSelected ? '' : cell.key);
                    }
                  }}
                  className={`flex flex-col h-8 w-8 sm:h-9 sm:w-9 min-w-0 items-center justify-center rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-[#8B5CF6] text-white shadow-sm ring-2 ring-[#E9A8D4]'
                      : count > 0
                      ? 'bg-[#F0E8FF] text-[#6D28D9] font-bold border border-[#E3D4F8] hover:shadow-xs hover:scale-105'
                      : isToday
                      ? 'ring-1.5 ring-[#8B5CF6] text-[#6D28D9] font-bold hover:bg-[#F0E8FF]'
                      : 'text-[#261B33] hover:bg-[#F0E8FF]/60'
                  }`}
                >
                  <span>{cell.day}</span>
                  {count > 0 && !isSelected && (
                    <span className="w-1 h-1 rounded-full bg-[#8B5CF6] mt-0.5" />
                  )}
                </button>
              </div>
            );
          })}
        </div>

        {/* Footer Info */}
        <div className="mt-4 pt-3 border-t border-[#E3D4F8]/60 flex items-center justify-between text-xs text-[#776A83] px-1">
          <div className="flex items-center gap-1.5">
            <span className="inline-block w-2.5 h-2.5 rounded-md bg-[#F0E8FF] border border-[#8B5CF6]/40" />
            <span className="font-medium text-[11px]">Important date</span>
          </div>
          {selectedKey && (
            <span className="text-[11px] font-semibold text-[#6D28D9]">
              {formatReadableDate(selectedKey)}
            </span>
          )}
        </div>
      </section>

      {/* Side Panel Section */}
      <section className="bg-white rounded-[1.75rem] p-6 sm:p-8 border border-[#E3D4F8] shadow-sm h-full flex flex-col min-h-[350px]">
        {displayKey && displayEvents.length > 0 ? (
          <>
            <div className="mb-5 flex items-center justify-between">
              <div>
                <h3 className="font-display tracking-wide text-xl uppercase text-[#261B33]">
                  {formatReadableDate(displayKey)}
                </h3>
                <p className="text-xs font-bold uppercase tracking-widest text-[#6D28D9] mt-1">
                  {displayEvents.length} IMPORTANT DATE{displayEvents.length > 1 ? 'S' : ''}
                </p>
              </div>
            </div>
            
            <div className="flex-1 space-y-4 overflow-y-auto pr-1">
              {displayEvents.map((event, i) => (
                <div key={event.id || i} className="bg-[#F9ECF5]/60 rounded-2xl p-5 border border-[#E3D4F8]">
                  <h4 className="text-base font-bold text-[#261B33] mb-3 leading-snug">
                    {event.reel?.title || 'Saved Opportunity'}
                  </h4>
                  
                  <div className="space-y-2 mb-4">
                    <div className="flex flex-col">
                      <span className="text-[10px] font-bold uppercase tracking-widest text-[#776A83]">Event</span>
                      <span className="text-sm font-medium text-[#261B33]">{event.label}</span>
                    </div>
                    
                    {event.reel?.analysis?.tags?.[0] && (
                      <div className="flex flex-col">
                        <span className="text-[10px] font-bold uppercase tracking-widest text-[#776A83]">Category</span>
                        <span className="text-sm font-medium text-[#261B33] capitalize">{event.reel.analysis.tags[0]}</span>
                      </div>
                    )}
                    
                    {event.reel?.author && (
                      <div className="flex flex-col">
                        <span className="text-[10px] font-bold uppercase tracking-widest text-[#776A83]">Provider</span>
                        <span className="text-sm font-medium text-[#261B33]">{event.reel.author}</span>
                      </div>
                    )}
                  </div>
                  
                  <button
                    type="button"
                    onClick={() => {
                      if (onViewOpportunity && event.reel?.reel_id) {
                        onViewOpportunity(event.reel.reel_id);
                      }
                    }}
                    className="w-full bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] hover:from-[#7C3AED] hover:to-[#5B21B6] text-white transition-all rounded-xl py-2.5 text-xs font-bold uppercase tracking-widest flex items-center justify-center gap-1.5 shadow-xs cursor-pointer"
                  >
                    View Opportunity &rarr;
                  </button>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-6">
            <div className="w-16 h-16 bg-[#F0E8FF] rounded-2xl flex items-center justify-center mb-4 border border-[#E3D4F8]">
              <CalendarDays size={24} className="text-[#8B5CF6]" />
            </div>
            <h3 className="font-display tracking-wide text-lg uppercase text-[#261B33] mb-2">
              IMPORTANT DATES
            </h3>
            <p className="text-[#776A83] text-sm font-medium max-w-[200px]">
              Hover over a highlighted date to view its opportunity details.
            </p>
          </div>
        )}
      </section>
    </div>
  );
}
