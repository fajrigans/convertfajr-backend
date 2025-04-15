// backend/index.js
const express = require('express');
const cors = require('cors');
const multer = require('multer');
const ffmpeg = require('fluent-ffmpeg');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = 5000;

// Middleware
app.use(cors());
app.use(express.json());
app.use('/converted', express.static(path.join(__dirname, 'converted')));

// Storage config
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads');
  },
  filename: (req, file, cb) => {
    cb(null, Date.now() + path.extname(file.originalname));
  }
});

const upload = multer({ storage });

// Route untuk upload & convert
app.post('/convert', upload.single('file'), (req, res) => {
  const file = req.file;
  const { format } = req.body;

  if (!file) return res.status(400).json({ error: 'File tidak ditemukan.' });

  const inputPath = file.path;
  const outputFilename = `${path.parse(file.filename).name}.${format.toLowerCase()}`;
  const outputPath = path.join(__dirname, 'converted', outputFilename);

  ffmpeg(inputPath)
    .output(outputPath)
    .on('end', () => {
      // Hapus file asli
      fs.unlinkSync(inputPath);
      res.json({ success: true, file: `/converted/${outputFilename}` });
    })
    .on('error', (err) => {
      console.error('Conversion error:', err);
      res.status(500).json({ error: 'Konversi gagal.' });
    })
    .run();
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Server jalan di http://localhost:${PORT}`);
});
