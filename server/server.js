const express = require('express');
const multer = require('multer');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const { exec } = require('child_process');

const app = express();
const PORT = 5000;

// Middleware
app.use(cors());
app.use(express.json());

// Setup Multer
const upload = multer({ dest: 'uploads/' });

// Route untuk konversi file
app.post('/api/convert', upload.single('file'), (req, res) => {
  const file = req.file;
  const targetFormat = req.body.format;

  if (!file || !targetFormat) {
    return res.status(400).json({ error: 'File dan format diperlukan' });
  }

  const originalExt = path.extname(file.originalname);
  const baseName = path.basename(file.originalname, originalExt);
  const outputFileName = `${baseName}.${targetFormat}`;
  const outputPath = path.join(__dirname, 'uploads', outputFileName);

  const command = `ffmpeg -i "${file.path}" "${outputPath}"`;

  exec(command, (err) => {
    if (err) {
      console.error('Konversi gagal:', err);
      return res.status(500).json({ error: 'Konversi gagal' });
    }

    // Kirim file hasil konversi
    res.download(outputPath, outputFileName, (err) => {
      // Hapus file sementara setelah dikirim
      fs.unlink(file.path, () => {});
      fs.unlink(outputPath, () => {});
      if (err) {
        console.error('Gagal mengirim file:', err);
      }
    });
  });
});

// Jalankan server
app.listen(PORT, () => {
  console.log(`Server berjalan di http://localhost:${PORT}`);
});
