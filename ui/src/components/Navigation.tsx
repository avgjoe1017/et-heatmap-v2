/**
 * Main navigation bar component.
 */

import { Link, useLocation } from 'react-router-dom';
import ThemeToggle from './ThemeToggle';

export default function Navigation() {
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const navLinkStyle = (path: string) => ({
    padding: '10px 20px',
    textDecoration: 'none',
    color: isActive(path) ? 'var(--primary)' : 'var(--text-primary)',
    fontWeight: isActive(path) ? 'bold' : 'normal',
    borderBottom: isActive(path) ? '3px solid var(--primary)' : '3px solid transparent',
    transition: 'all 0.2s ease',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    fontSize: '15px'
  });

  const navLinkHoverStyle = {
    ':hover': {
      color: '#1976d2',
      backgroundColor: '#f5f5f5'
    }
  };

  return (
    <nav style={{
      backgroundColor: 'var(--bg-primary)',
      borderBottom: '2px solid var(--border-color)',
      boxShadow: '0 2px 4px var(--shadow)',
      position: 'sticky',
      top: 0,
      zIndex: 1000,
      transition: 'background-color 0.3s ease, border-color 0.3s ease'
    }}>
      <div style={{
        maxWidth: '1400px',
        margin: '0 auto',
        padding: '0 20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        {/* Logo/Brand */}
        <Link to="/" style={{
          textDecoration: 'none',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '12px 0'
        }}>
          <div style={{
            fontSize: '24px',
            fontWeight: 'bold',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}>
            ❤️ Entertainment Feelings
          </div>
        </Link>

        {/* Navigation Links */}
        <div style={{ display: 'flex', gap: '8px' }}>
          <Link to="/" style={navLinkStyle('/')}>
            📊 Heatmap
          </Link>
          <Link to="/runs" style={navLinkStyle('/runs')}>
            ⚙️ Pipeline Runs
          </Link>
          <Link to="/resolve-queue" style={navLinkStyle('/resolve-queue')}>
            🔍 Resolve Queue
            {/* Could add badge with count here */}
          </Link>
        </div>

        {/* Right Side Actions */}
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <ThemeToggle />
          <div style={{
            fontSize: '12px',
            color: 'var(--text-secondary)',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}>
            <kbd style={{
              padding: '2px 6px',
              backgroundColor: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: '4px',
              fontSize: '10px',
              color: 'var(--text-primary)'
            }}>
              /
            </kbd>
            Search
          </div>
        </div>
      </div>
    </nav>
  );
}
