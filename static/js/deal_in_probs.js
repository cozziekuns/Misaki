const SUIT_TO_FILENAME = {
  'm': 'Man',
  'p': 'Pin',
  's': 'Sou',
  'z': 'Ji',
};

const tileStringToFilename = (tileString) => {
  return SUIT_TO_FILENAME[tileString[1]] + tileString[0];
}

const refreshTileImages = (discardString) => { 
  for (let i = 0; i < Math.floor(discardString.length / 3); i++) {
    const tileString = discardString.substring(i * 3, i * 3 + 3);
    
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

