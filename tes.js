const objectItems = require('./tes.json');

const simplified = objectItems.map(b => ({
  id: b.id,
  type: b.type,
  content: b.content
}));

function getIdByContent(content) {
  const match = simplified.find(b => b.content === content);
  return match ? match.id : null;
}

const targetId = getIdByContent("Rontgen Thoraks");
console.log(targetId)
