from flask import Flask, render_template, request, jsonify
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
from sklearn.cluster import KMeans

app = Flask(__name__)

# --- Spotify API Setup ---
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id='ca83541e50934d62925b08dff1c02a8f',
    client_secret='f2627f8d62094d3eb532aa0178f661b1'
))

def fetch_tracks(vibe, limit=30):
    results = sp.search(q=vibe, type='track', limit=limit)
    tracks = []
    for track in results['tracks']['items']:
        track_id = track['id']
        features = sp.audio_features(track_id)[0]  # audio features
        if features:
            tracks.append({
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'url': track['external_urls']['spotify'],
                'danceability': features['danceability'],
                'energy': features['energy'],
                'valence': features['valence'],
                'tempo': features['tempo']
            })
    return pd.DataFrame(tracks)

def cluster_tracks(df, n_clusters=3):
    features = df[['danceability', 'energy', 'valence', 'tempo']]
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
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
    # pick a random cluster to return as "recommended playlist"
    cluster_id = df['cluster'].sample(1).iloc[0]
    recommendations = df[df['cluster'] == cluster_id].sample(min(5, len(df))).to_dict(orient='records')
    return jsonify(recommendations)

if __name__ == "__main__":
    app.run(debug=True)
