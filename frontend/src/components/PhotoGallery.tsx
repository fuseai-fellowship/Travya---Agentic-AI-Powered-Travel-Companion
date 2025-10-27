import React, { useState, useEffect } from 'react';
import { FiCamera, FiExternalLink, FiRefreshCw, FiAlertCircle } from 'react-icons/fi';

interface PhotoSource {
  id: string;
  url: string;
  thumbnail_url: string;
  photographer_name: string;
  photographer_url: string;
  source: string;
  width: number;
  height: number;
  description?: string;
  download_tracked: boolean;
}

interface GalleryPlace {
  id: string;
  name: string;
  place_type: string;
  caption: string;
  search_query: string;
  priority: number;
  photos: PhotoSource[];
}

interface PhotoGallery {
  id: string;
  trip_id: string;
  title: string;
  description?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  total_places: number;
  total_photos: number;
  created_at: string;
  updated_at: string;
}

interface PhotoGalleryProps {
  tripId: string;
  onGenerateGallery?: () => void;
}

const PhotoGalleryComponent: React.FC<PhotoGalleryProps> = ({ tripId, onGenerateGallery }) => {
  const [gallery, setGallery] = useState<PhotoGallery | null>(null);
  const [places, setPlaces] = useState<GalleryPlace[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [selectedPlace, setSelectedPlace] = useState<GalleryPlace | null>(null);
  const [selectedPhoto, setSelectedPhoto] = useState<PhotoSource | null>(null);

  useEffect(() => {
    loadGallery();
  }, [tripId]);

  const loadGallery = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      
      // Get galleries for this trip
      const response = await fetch(`http://localhost:8000/api/v1/photo-gallery/trip/${tripId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        console.log('🔍 Gallery data from API:', data);
        if (data.data && data.data.length > 0) {
          const galleryData = data.data[0]; // Get the first gallery
          console.log('📊 Gallery status:', galleryData.status);
          console.log('📊 Gallery data:', galleryData);
          setGallery(galleryData);
          
          // Load places for this gallery
          await loadPlaces(galleryData.id);
        } else {
          console.log('❌ No gallery data found');
        }
      } else {
        console.error('❌ Failed to load gallery:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('Error loading gallery:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadPlaces = async (galleryId: string) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/v1/photo-gallery/${galleryId}/places`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        const placesData = data.data || [];
        
        // Load photos for each place
        const placesWithPhotos = await Promise.all(
          placesData.map(async (place: any) => {
            try {
              const photosResponse = await fetch(`http://localhost:8000/api/v1/photo-gallery/${galleryId}/places/${place.id}/photos`, {
                headers: {
                  'Authorization': `Bearer ${token}`,
                  'Content-Type': 'application/json',
                },
              });
              
              if (photosResponse.ok) {
                const photosData = await photosResponse.json();
                return {
                  ...place,
                  photos: photosData.data || []
                };
              } else {
                return {
                  ...place,
                  photos: []
                };
              }
            } catch (error) {
              console.error(`Error loading photos for place ${place.id}:`, error);
              return {
                ...place,
                photos: []
              };
            }
          })
        );
        
        setPlaces(placesWithPhotos);
      }
    } catch (error) {
      console.error('Error loading places:', error);
    }
  };

  const deleteGallery = async (galleryId: string) => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`http://localhost:8000/api/v1/photo-gallery/${galleryId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        console.log('✅ Gallery deleted successfully');
        return true;
      } else {
        console.error('❌ Failed to delete gallery:', response.status, response.statusText);
        return false;
      }
    } catch (error) {
      console.error('Error deleting gallery:', error);
      return false;
    }
  };

  const generateGallery = async (isRetry = false) => {
    try {
      setGenerating(true);
      if (isRetry) {
        setRetryCount(prev => prev + 1);
      }
      
      const token = localStorage.getItem('access_token');
      
      const response = await fetch(`http://localhost:8000/api/v1/photo-gallery/generate/${tripId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const galleryData = await response.json();
        setGallery(galleryData);
        setRetryCount(0); // Reset retry count on success
        
        // Start polling for updates
        pollGalleryStatus(galleryData.id);
        
        if (onGenerateGallery) {
          onGenerateGallery();
        }
      } else {
        const error = await response.json();
        console.error('Gallery generation error:', error);
        
        // If gallery already exists, check if it's failed and delete it
        if (error.detail === 'Photo gallery already exists for this trip') {
          console.log('Gallery already exists, checking status...');
          
          // Load the gallery to check its status
          const token = localStorage.getItem('access_token');
          const galleryResponse = await fetch(`http://localhost:8000/api/v1/photo-gallery/trip/${tripId}`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });
          
          if (galleryResponse.ok) {
            const galleryData = await galleryResponse.json();
            if (galleryData.data && galleryData.data.length > 0) {
              const existingGallery = galleryData.data[0];
              console.log('📊 Existing gallery status:', existingGallery.status);
              
              // If the existing gallery is failed, delete it and try again
              if (existingGallery.status === 'failed') {
                console.log('Gallery is failed, deleting and regenerating...');
                const deleted = await deleteGallery(existingGallery.id);
                if (deleted) {
                  // Try generating again after deletion
                  setTimeout(() => generateGallery(isRetry), 1000);
                  return;
                }
              } else {
                // Gallery exists and is not failed, load it
                await loadGallery();
              }
            }
          }
          return;
        }
        
        // If user doesn't have permission, show appropriate message
        if (error.detail === 'You don\'t have permission to access this trip') {
          console.log('User does not have permission to access this trip');
          setGallery({
            id: '',
            trip_id: tripId,
            title: 'Photo Gallery',
            description: 'You don\'t have permission to access this trip',
            status: 'failed',
            total_places: 0,
            total_photos: 0,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          });
          return;
        }
        
        // Set gallery to failed state for proper error display
        setGallery({
          id: '',
          trip_id: tripId,
          title: 'Photo Gallery',
          description: 'Failed to generate',
          status: 'failed',
          total_places: 0,
          total_photos: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        });
      }
    } catch (error) {
      console.error('Error generating gallery:', error);
      
      // Set gallery to failed state for proper error display
      setGallery({
        id: '',
        trip_id: tripId,
        title: 'Photo Gallery',
        description: 'Failed to generate',
        status: 'failed',
        total_places: 0,
        total_photos: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      });
    } finally {
      setGenerating(false);
    }
  };

  const pollGalleryStatus = async (galleryId: string) => {
    const maxAttempts = 30; // Poll for up to 5 minutes
    let attempts = 0;
    
    const poll = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`http://localhost:8000/api/v1/photo-gallery/${galleryId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const galleryData = await response.json();
          setGallery(galleryData);
          
          if (galleryData.status === 'completed') {
            await loadPlaces(galleryId);
            return;
          } else if (galleryData.status === 'failed') {
            alert('Gallery generation failed. Please try again.');
            return;
          }
        }
        
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 10000); // Poll every 10 seconds
        }
      } catch (error) {
        console.error('Error polling gallery status:', error);
      }
    };
    
    poll();
  };

  const trackPhotoDownload = async (galleryId: string, photoId: string) => {
    try {
      const token = localStorage.getItem('access_token');
      await fetch(`http://localhost:8000/api/v1/photo-gallery/${galleryId}/photos/${photoId}/track-download`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
    } catch (error) {
      console.error('Error tracking download:', error);
    }
  };

  const openPhotoModal = (place: GalleryPlace, photo: PhotoSource) => {
    setSelectedPlace(place);
    setSelectedPhoto(photo);
    
    // Track download for Unsplash compliance
    if (gallery && photo.source === 'unsplash' && !photo.download_tracked) {
      trackPhotoDownload(gallery.id, photo.id);
    }
  };

  const closePhotoModal = () => {
    setSelectedPlace(null);
    setSelectedPhoto(null);
  };

  if (loading) {
    return (
      <div className="photo-gallery-loading">
        <div className="loading-spinner">
          <FiRefreshCw className="spinning" />
        </div>
        <p>Loading photo gallery...</p>
      </div>
    );
  }

  if (!gallery) {
    return (
      <div className="photo-gallery-empty">
        <FiCamera className="empty-icon" />
        <h3>No Photo Gallery</h3>
        <p>Generate a photo gallery to see beautiful images of your trip destinations.</p>
        <button 
          className="btn-primary" 
          onClick={() => generateGallery(false)}
          disabled={generating}
        >
          {generating ? (
            <>
              <FiRefreshCw className="spinning" />
              Generating Gallery...
            </>
          ) : (
            <>
              <FiCamera />
              Generate Photo Gallery
            </>
          )}
        </button>
      </div>
    );
  }

  if (gallery.status === 'processing') {
    return (
      <div className="photo-gallery-processing">
        <div className="processing-spinner">
          <FiRefreshCw className="spinning" />
        </div>
        <h3>Generating Photo Gallery</h3>
        <p>We're analyzing your itinerary and fetching beautiful photos...</p>
        <div className="processing-stats">
          <p>Status: {gallery.status}</p>
        </div>
      </div>
    );
  }

  if (gallery.status === 'failed') {
    const isPermissionError = gallery.description === 'You don\'t have permission to access this trip';
    
    return (
      <div className="photo-gallery-error">
        <FiAlertCircle className="error-icon" />
        <h3>{isPermissionError ? 'Access Denied' : 'Gallery Generation Failed'}</h3>
        <p>{isPermissionError ? 'You don\'t have permission to access this trip\'s photo gallery.' : 'There was an error generating your photo gallery. Please try again.'}</p>
        {retryCount > 0 && !isPermissionError && (
          <p className="retry-info">Retry attempt: {retryCount}</p>
        )}
        {!isPermissionError && (
          <button 
            className="btn-primary" 
            onClick={() => generateGallery(true)}
            disabled={generating}
          >
            {generating ? (
              <>
                <FiRefreshCw className="spinning" />
                Retrying...
              </>
            ) : (
              <>
                <FiRefreshCw />
                Try Again
              </>
            )}
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="photo-gallery">
      <div className="gallery-header">
        <div className="gallery-info">
          <h2>{gallery.title}</h2>
          <p>{gallery.description}</p>
          <div className="gallery-stats">
            <span>{gallery.total_places} places</span>
            <span>•</span>
            <span>{gallery.total_photos} photos</span>
          </div>
        </div>
        <button 
          className="btn-secondary" 
          onClick={() => generateGallery(true)}
          disabled={generating}
        >
          {generating ? (
            <>
              <FiRefreshCw className="spinning" />
              Regenerating...
            </>
          ) : (
            <>
              <FiRefreshCw />
              Regenerate
            </>
          )}
        </button>
      </div>

      <div className="gallery-places">
        {places.map((place) => (
          <div key={place.id} className="place-section">
            <div className="place-header">
              <h3>{place.name}</h3>
              <span className={`place-type ${place.place_type}`}>
                {place.place_type.replace('_', ' ')}
              </span>
            </div>
            <p className="place-caption">{place.caption}</p>
            
            <div className="place-photos">
              {place.photos && place.photos.length > 0 ? (
                place.photos.map((photo) => (
                  <div 
                    key={photo.id} 
                    className="photo-item"
                    onClick={() => openPhotoModal(place, photo)}
                  >
                    <img 
                      src={photo.thumbnail_url} 
                      alt={photo.description || place.name}
                      loading="lazy"
                    />
                    <div className="photo-overlay">
                      <FiExternalLink />
                    </div>
                  </div>
                ))
              ) : (
                <div className="no-photos">
                  <p>No photos available for this place</p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Photo Modal */}
      {selectedPhoto && selectedPlace && (
        <div className="photo-modal-overlay" onClick={closePhotoModal}>
          <div className="photo-modal" onClick={(e) => e.stopPropagation()}>
            <div className="photo-modal-header">
              <h3>{selectedPlace.name}</h3>
              <button className="close-btn" onClick={closePhotoModal}>
                ×
              </button>
            </div>
            
            <div className="photo-modal-content">
              <img 
                src={selectedPhoto.url} 
                alt={selectedPhoto.description || selectedPlace.name}
                className="modal-photo"
              />
              
              <div className="photo-info">
                <p className="photo-description">
                  {selectedPhoto.description || selectedPlace.caption}
                </p>
                
                <div className="photo-credits">
                  <p>
                    Photo by{' '}
                    <a 
                      href={selectedPhoto.photographer_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="photographer-link"
                    >
                      {selectedPhoto.photographer_name}
                    </a>
                    {' '}on{' '}
                    <a 
                      href={selectedPhoto.source === 'unsplash' ? 'https://unsplash.com' : 'https://pexels.com'} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="source-link"
                    >
                      {selectedPhoto.source === 'unsplash' ? 'Unsplash' : 'Pexels'}
                    </a>
                  </p>
                  
                  <div className="photo-actions">
                    <a 
                      href={selectedPhoto.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="btn-secondary"
                    >
                      <FiExternalLink />
                      View Full Size
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PhotoGalleryComponent;
