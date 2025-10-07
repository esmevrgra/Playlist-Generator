from flask import Flask, render_template, request, jsonify
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
from sklearn.cluster import KMeans
import os # Keep this import for best practice structure

app = Flask(__name__)

# --- Spotify API Setup ---
# *** CRITICAL FIX: Use your Client ID and replace the fake secret with your actual secret ***
# NOTE: It is strongly recommended to use environment variables for the secret, 
# but for a quick fix, replace the SECRET below:

CLIENT_ID = 'ca83541e50934d62925b08dff1c02a8f'
CLIENT_SECRET = 'f2627f8d62094d3eb532aa0178f661b1' # <--- REPLACE THIS LINE!

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET
))

def fetch_tracks(vibe, limit=30):
    """Searches Spotify for tracks based on vibe and fetches their audio features."""
    results = sp.search(q=vibe, type='track', limit=limit)
    tracks = []
    
    # Efficiently fetch features for all tracks at once
    track_ids = [track['id'] for track in results['tracks']['items']]
    features_list = sp.audio_features(track_ids)
    
    for track, features in zip(results['tracks']['items'], features_list):
        if features:
            tracks.append({
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'url': track['external_urls']['spotify'],
                'danceability': features.get('danceability'),
                'energy': features.get('energy'),
                'valence': features.get('valence'),
                'tempo': features.get('tempo')
            })
    return pd.DataFrame(tracks)

def cluster_tracks(df, n_clusters=3):
    """Performs K-Means clustering on the track features."""
    if len(df) < n_clusters:
        df['cluster'] = 0
        return df

    features = df[['danceability', 'energy', 'valence', 'tempo']]
    # Added n_init='auto' to suppress scikit-learn warnings
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto') 
    df['cluster'] = kmeans.fit_predict(features)
    return df

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    vibe = request.json.get('vibe', '')
    if not vibe:
        return jsonify([])

    df = fetch_tracks(vibe, limit=30)
    
    if df.empty:
        return jsonify([])

    df = cluster_tracks(df)
    
    if 'cluster' in df.columns:
        # Pick a random cluster ID to return as the "recommended playlist"
        cluster_id = df['cluster'].sample(1).iloc[0]
        
        # Filter tracks for the chosen cluster and sample up to 5 songs
        recommendations = df[df['cluster'] == cluster_id].sample(min(5, len(df))).to_dict(orient='records')
        return jsonify(recommendations)
    else:
        # Fallback if clustering was skipped
        return df.sample(min(5, len(df))).to_dict(orient='records')

if __name__ == "__main__":
    app.run(debug=True, port=8080)  # <-- Added port=8080