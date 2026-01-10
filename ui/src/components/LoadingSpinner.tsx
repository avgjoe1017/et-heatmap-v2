/**
 * Loading spinner component.
 */

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  text?: string;
}

export default function LoadingSpinner({ size = 'medium', text }: LoadingSpinnerProps) {
  const sizes = {
    small: 24,
    medium: 40,
    large: 64
  };

  const spinnerSize = sizes[size];

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '12px',
      padding: '20px'
    }}>
      <div
        style={{
          width: `${spinnerSize}px`,
          height: `${spinnerSize}px`,
          border: `${Math.max(2, spinnerSize / 10)}px solid #f3f3f3`,
          borderTop: `${Math.max(2, spinnerSize / 10)}px solid #1976d2`,
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }}
      />
      {text && <p style={{ margin: 0, color: '#666', fontSize: '14px' }}>{text}</p>}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
