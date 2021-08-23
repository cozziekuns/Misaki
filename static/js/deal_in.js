const tedashiButton = document.getElementById('tedashi');
const tsumogiriButton = document.getElementById('tsumogiri');
const riichiBox = document.getElementById("riichi");
const discardInput = document.getElementById("discards");

const SUIT_TO_FILENAME = {
  'm': 'Man',
  'p': 'Pin',
  's': 'Sou',
  'z': 'Ji',
};


const tileStringToFilename = (tileString) => {
  return SUIT_TO_FILENAME[tileString[1]] + tileString[0];
}

const clearTileImages = () => {
  for (let i = 0; i < 21; i++) {
    const discardImage = document.getElementById("discard-" + i.toString());
    const discardBackImage = document.getElementById("discard-back-" + i.toString());

    discardImage.src = 'static/img/tiles/Blank.png';

    discardImage.classList.remove('tsumogiri');
    discardBackImage.classList.remove('tsumogiri');
    
    discardImage.classList.remove('riichi');
    discardBackImage.classList.remove('riichi');
  }
}

const refreshTileImages = () => { 
  for (let i = 0; i < Math.floor(discardInput.value.length / 3); i++) {
    const tileString = discardInput.value.substring(i * 3, i * 3 + 3);
    
    const discardImage = document.getElementById("discard-" + i.toString());
    const discardBackImage = document.getElementById("discard-back-" + i.toString());

    discardImage.src = "static/img/tiles/" + tileStringToFilename(tileString) + ".png";

    if (tileString[2] == 't' || tileString[2] == 'r') {
      discardImage.classList.add('tsumogiri');
      discardBackImage.classList.add('tsumogiri');
    }

    if (tileString[2] == 'r' || tileString[2] == 'R') {
      discardImage.classList.add('riichi');
      discardBackImage.classList.add('riichi');
    }
  }
}

const addTile = (tile) => {
  if (discardInput.value.length >= 63) {
    return;
  }

  const tedashi = tedashiButton.checked;
  const riichi = riichiBox.checked;

  let modifier = (riichi ? 'r' : 't');

  if (tedashi) {
    modifier = modifier.toUpperCase();
  }

  discardInput.value += tile + modifier;

  if (riichi) {
    tedashiButton.checked = false;
    tsumogiriButton.checked = true;
    riichiBox.checked = false;
  }

  refreshTileImages();
}

const removeTile = () => {
  discardInput.value = discardInput.value.substring(0, discardInput.value.length - 3);

  clearTileImages();
  refreshTileImages();
}

const clearTiles = () => {
  discardInput.value = '';

  clearTileImages();
  refreshTileImages();
}

clearTileImages();
refreshTileImages();
