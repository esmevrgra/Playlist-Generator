async function getPlaylist() {
  const vibe = document.getElementById('vibe').value;

  const response = await fetch('/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ vibe })
  });

  const songs = await response.json();

  const playlistDiv = document.getElementById('playlist');
  playlistDiv.innerHTML = songs.map(s =>
      `<p>🎧 <a href="${s.url}" target="_blank">${s.name} by ${s.artist}</a></p>`
  ).join('');
}
