const express = require("express");
const cors = require("cors");
const multer = require("multer");
const path = require("path");
const fs = require("fs");

const app = express();
const port = process.env.PORT || 5000;

// Middleware CORS
app.use(cors());

// Middleware untuk menerima form-data
const upload = multer({ dest: "uploads/" });

// Route root biar gak "Cannot GET /"
app.get("/", (req, res) => {
  res.send("Backend aktif 🚀");
});

// Route convert
app.post("/api/convert", upload.single("file"), (req, res) => {
  const file = req.file;
  const format = req.body.format;

  if (!file || !format) {
    return res.status(400).json({ error: "File dan format dibutuhkan" });
  }

  const ext = format.toLowerCase();
  const newFileName = `${file.filename}.${ext}`;
  const newPath = path.join("uploads", newFileName);

  fs.rename(file.path, newPath, (err) => {
    if (err) {
      console.error("❌ Gagal rename file:", err);
      return res.status(500).json({ error: "Konversi gagal" });
    }

    const fileUrl = `${req.protocol}://${req.get("host")}/uploads/${newFileName}`;
    res.json({ downloadUrl: fileUrl });
  });
});

// Serve folder uploads
app.use("/uploads", express.static(path.join(__dirname, "../uploads")));

app.listen(port, () => {
  console.log(`Server berjalan di http://localhost:${port}`);
});
