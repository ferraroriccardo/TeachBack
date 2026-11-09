// Loads the slide files listed in <main data-slides>, then starts the slide player.
// Copied to assets/loader.js by split_deck.py.
(async function () {
  const deck = document.getElementById('deck')
  const files = deck.dataset.slides.split(' ')
  try {
    const [motion, ...slides] = await Promise.all([
      fetch('assets/motion.json').then(r => r.json()),
      ...files.map(f => fetch(f).then(r => {
        if (!r.ok) throw new Error(`${f}: ${r.status}`)
        return r.text()
      })),
    ])
    deck.innerHTML = slides.join('\n')
    window.DECK_MOTION = motion
    const player = document.createElement('script')
    player.src = 'assets/deck.js'
    document.body.appendChild(player)
  } catch (err) {
    deck.innerHTML = '<p style="color:#fff;font:18px system-ui;padding:40px">' +
      'The slides could not be loaded (' + err.message + '). Open this page through a web server, ' +
      'for example <code>python -m server</code> and then /presentation/.</p>'
  }
})()
