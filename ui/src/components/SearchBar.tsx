/**
 * Entity search bar with autocomplete.
 */

import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

interface SearchBarProps {
  entities?: Array<{
    entity_id: string;
    name: string;
    type: string;
  }>;
  placeholder?: string;
  compact?: boolean;
}

export default function SearchBar({ entities = [], placeholder = "Search entities...", compact = false }: SearchBarProps) {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const navigate = useNavigate();
  const searchRef = useRef<HTMLDivElement>(null);

  // Filter entities based on query
  const filteredEntities = query.length > 0
    ? entities.filter(entity =>
        entity.name.toLowerCase().includes(query.toLowerCase()) ||
        entity.type.toLowerCase().includes(query.toLowerCase())
      ).slice(0, 10) // Limit to 10 results
    : [];

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Focus search on '/' key
      if (e.key === '/' && !isOpen) {
        e.preventDefault();
        const input = searchRef.current?.querySelector('input');
        input?.focus();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [isOpen]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    setIsOpen(true);
    setSelectedIndex(0);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev =>
          prev < filteredEntities.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : 0);
        break;
      case 'Enter':
        e.preventDefault();
        if (filteredEntities.length > 0) {
          selectEntity(filteredEntities[selectedIndex]);
        }
        break;
      case 'Escape':
        e.preventDefault();
        setIsOpen(false);
        setQuery('');
        break;
    }
  };

  const selectEntity = (entity: { entity_id: string; name: string; type: string }) => {
    navigate(`/entity/${entity.entity_id}`);
    setQuery('');
    setIsOpen(false);
  };

  const getTypeColor = (type: string) => {
    const colors: { [key: string]: string } = {
      PERSON: '#1976d2',
      SHOW: '#e91e63',
      FILM: '#9c27b0',
      FRANCHISE: '#ff9800',
      STREAMER: '#4caf50',
      BRAND: '#f44336',
      CHARACTER: '#00bcd4',
      COUPLE: '#ff5722'
    };
    return colors[type] || '#999';
  };

  return (
    <div ref={searchRef} style={{ position: 'relative', width: compact ? '300px' : '100%' }}>
      <div style={{ position: 'relative' }}>
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          onFocus={() => query.length > 0 && setIsOpen(true)}
          placeholder={placeholder}
          style={{
            width: '100%',
            padding: compact ? '8px 36px 8px 12px' : '12px 40px 12px 16px',
            border: '2px solid #e0e0e0',
            borderRadius: compact ? '20px' : '24px',
            fontSize: compact ? '13px' : '14px',
            outline: 'none',
            transition: 'all 0.2s ease'
          }}
          onFocusCapture={(e) => {
            e.target.style.borderColor = '#1976d2';
            e.target.style.boxShadow = '0 0 0 3px rgba(25, 118, 210, 0.1)';
          }}
          onBlurCapture={(e) => {
            e.target.style.borderColor = '#e0e0e0';
            e.target.style.boxShadow = 'none';
          }}
        />
        <div style={{
          position: 'absolute',
          right: '12px',
          top: '50%',
          transform: 'translateY(-50%)',
          color: '#999',
          pointerEvents: 'none',
          fontSize: compact ? '16px' : '18px'
        }}>
          🔍
        </div>
      </div>

      {/* Autocomplete Dropdown */}
      {isOpen && filteredEntities.length > 0 && (
        <div style={{
          position: 'absolute',
          top: 'calc(100% + 8px)',
          left: 0,
          right: 0,
          backgroundColor: 'white',
          border: '2px solid #e0e0e0',
          borderRadius: '12px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          maxHeight: '400px',
          overflowY: 'auto',
          zIndex: 1000
        }}>
          {filteredEntities.map((entity, index) => (
            <div
              key={entity.entity_id}
              onClick={() => selectEntity(entity)}
              style={{
                padding: '12px 16px',
                cursor: 'pointer',
                backgroundColor: index === selectedIndex ? '#f5f5f5' : 'white',
                borderBottom: index < filteredEntities.length - 1 ? '1px solid #f0f0f0' : 'none',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}
              onMouseEnter={() => setSelectedIndex(index)}
            >
              <div>
                <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '4px' }}>
                  {entity.name}
                </div>
                <div style={{
                  display: 'inline-block',
                  backgroundColor: getTypeColor(entity.type) + '20',
                  color: getTypeColor(entity.type),
                  padding: '2px 8px',
                  borderRadius: '10px',
                  fontSize: '11px',
                  fontWeight: 'bold'
                }}>
                  {entity.type}
                </div>
              </div>
              <div style={{ color: '#999', fontSize: '18px' }}>→</div>
            </div>
          ))}

          {/* Keyboard hints */}
          <div style={{
            padding: '8px 16px',
            borderTop: '1px solid #f0f0f0',
            backgroundColor: '#f9f9f9',
            fontSize: '11px',
            color: '#666',
            display: 'flex',
            gap: '12px',
            justifyContent: 'center'
          }}>
            <span><kbd style={{ padding: '2px 4px', backgroundColor: 'white', border: '1px solid #ccc', borderRadius: '3px' }}>↑↓</kbd> Navigate</span>
            <span><kbd style={{ padding: '2px 4px', backgroundColor: 'white', border: '1px solid #ccc', borderRadius: '3px' }}>↵</kbd> Select</span>
            <span><kbd style={{ padding: '2px 4px', backgroundColor: 'white', border: '1px solid #ccc', borderRadius: '3px' }}>ESC</kbd> Close</span>
          </div>
        </div>
      )}

      {/* No results */}
      {isOpen && query.length > 0 && filteredEntities.length === 0 && (
        <div style={{
          position: 'absolute',
          top: 'calc(100% + 8px)',
          left: 0,
          right: 0,
          backgroundColor: 'white',
          border: '2px solid #e0e0e0',
          borderRadius: '12px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          padding: '24px',
          textAlign: 'center',
          color: '#999',
          zIndex: 1000
        }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>🔍</div>
          <div style={{ fontSize: '14px' }}>No entities found for "{query}"</div>
        </div>
      )}
    </div>
  );
}
