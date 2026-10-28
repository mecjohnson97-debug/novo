import React from 'react';
import { GoogleMap, Marker, useJsApiLoader } from '@react-google-maps/api';
import { Loader2 } from 'lucide-react';

const PARIS = { lat: 48.8566, lng: 2.3522 };
const containerStyle = { width: '100%', height: '100%' };

export default function GoogleMapComponent({ apiKey, locations = [], userLocation, onMarkerClick }) {
  const { isLoaded, loadError } = useJsApiLoader({ id: 'google-map-script', googleMapsApiKey: apiKey });

  if (loadError) {
    return (
      <div className="flex items-center justify-center h-full bg-red-50 text-red-600 p-4 text-sm" data-testid="google-map-error">
        Não foi possível carregar o Google Maps. Verifique a chave da API.
      </div>
    );
  }

  if (!isLoaded) {
    return (
      <div className="flex items-center justify-center h-full" data-testid="google-map-loading">
        <Loader2 className="animate-spin text-blue-500" size={40} />
      </div>
    );
  }

  return (
    <GoogleMap mapContainerStyle={containerStyle} center={userLocation || PARIS} zoom={userLocation ? 14 : 12}>
      {userLocation && (
        <Marker
          position={userLocation}
          title="Sua localização"
          icon={{ url: 'https://maps.google.com/mapfiles/ms/icons/blue-dot.png' }}
        />
      )}
      {locations.filter(l => l.lat && l.lng).map(location => (
        <Marker
          key={location.id}
          position={{ lat: Number(location.lat), lng: Number(location.lng) }}
          title={location.name}
          onClick={() => onMarkerClick?.(location)}
          icon={{ url: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png' }}
        />
      ))}
    </GoogleMap>
  );
}
