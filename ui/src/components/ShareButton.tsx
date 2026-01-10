/**
 * Share button component that generates shareable URLs.
 */

import { useState } from 'react';
import { getShareableURL, type URLState } from '../utils/urlState';

interface ShareButtonProps {
  state: Partial<URLState>;
  label?: string;
}

export default function ShareButton({ state, label = 'Share' }: ShareButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleShare = async () => {
    const shareableURL = getShareableURL(state);

    // Try using Web Share API if available (mobile browsers)
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'ET Heatmap',
          text: 'Check out this Entertainment Feelings Heatmap view',
          url: shareableURL,
        });
        return;
      } catch (err) {
        // User cancelled or error occurred, fall back to clipboard
        if ((err as Error).name !== 'AbortError') {
          console.error('Error sharing:', err);
        }
      }
    }

    // Fallback to clipboard
    try {
      await navigator.clipboard.writeText(shareableURL);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
      // Fallback: prompt with URL
      alert(`Share this URL:\n${shareableURL}`);
    }
  };

  return (
    <button
      onClick={handleShare}
      style={{
        padding: '8px 16px',
        border: copied ? '2px solid #4caf50' : '2px solid #1976d2',
        backgroundColor: copied ? '#e8f5e9' : 'white',
        color: copied ? '#4caf50' : '#1976d2',
        borderRadius: '8px',
        cursor: 'pointer',
        fontSize: '14px',
        fontWeight: 'bold',
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
        transition: 'all 0.3s ease'
      }}
      title={copied ? 'URL copied to clipboard!' : 'Copy shareable link'}
    >
      {copied ? '✓ Copied!' : '🔗 Share'}
      {!copied && <span style={{ fontSize: '12px' }}>{label}</span>}
    </button>
  );
}
