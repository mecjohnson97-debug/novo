import React from 'react';

const API = process.env.REACT_APP_BACKEND_URL;

export const avatarSrc = (userId, version) => (userId && version ? `${API}/api/users/${userId}/avatar?v=${version}` : null);

export default function Avatar({ userId, version, name, size = 40, className = '', testId }) {
  const src = avatarSrc(userId, version);
  const style = { width: size, height: size, fontSize: Math.round(size * 0.4) };
  if (src) {
    return <img src={src} alt={name || ''} loading="lazy" style={style} className={`flex-shrink-0 rounded-full object-cover ${className}`} data-testid={testId} />;
  }
  return (
    <div style={style} className={`feed-avatar flex-shrink-0 ${className}`} data-testid={testId}>
      {(name || '?').charAt(0).toUpperCase()}
    </div>
  );
}
