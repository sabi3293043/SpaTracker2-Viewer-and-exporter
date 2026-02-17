const http = require('http')
const fs = require('fs')
const path = require('path')
const { formidable } = require('formidable')
const { spawn } = require('child_process')
const crypto = require('crypto')

const PORT = process.argv[2] || 8080
const UPLOAD_DIR = path.join(__dirname, 'uploads')
const PROCESSED_DIR = path.join(__dirname, 'processed')

// Ensure directories exist
if (!fs.existsSync(UPLOAD_DIR)) {
  fs.mkdirSync(UPLOAD_DIR, { recursive: true })
}
if (!fs.existsSync(PROCESSED_DIR)) {
  fs.mkdirSync(PROCESSED_DIR, { recursive: true })
}

// Store processing status
const processingStatus = new Map()

const mimeTypes = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.bin': 'application/octet-stream'
}

const server = http.createServer((req, res) => {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type')

  if (req.method === 'OPTIONS') {
    res.writeHead(200)
    res.end()
    return
  }

  // Route handling
  if (req.method === 'GET' && req.url === '/') {
    serveFile(res, path.join(__dirname, 'index.html'))
    return
  }

  if (req.method === 'GET' && req.url.startsWith('/viewer/')) {
    const viewerId = req.url.split('/')[2]
    const viewerHtml = path.join(PROCESSED_DIR, `${viewerId}_viewer.html`)
    if (fs.existsSync(viewerHtml)) {
      serveFile(res, viewerHtml)
    } else {
      res.writeHead(404)
      res.end('Viewer not found')
    }
    return
  }

  if (req.method === 'GET' && req.url.startsWith('/data/')) {
    const dataId = req.url.split('/')[2]
    const dataFile = path.join(PROCESSED_DIR, `${dataId}.bin`)
    if (fs.existsSync(dataFile)) {
      serveFile(res, dataFile)
    } else {
      res.writeHead(404)
      res.end('Data not found')
    }
    return
  }

  if (req.method === 'POST' && req.url === '/api/upload') {
    handleUpload(req, res)
    return
  }

  if (req.method === 'POST' && req.url === '/api/process') {
    handleProcess(req, res)
    return
  }

  if (req.method === 'GET' && req.url === '/api/status') {
    const urlParams = new URL(req.url, `http://localhost:${PORT}`)
    const taskId = urlParams.searchParams.get('id')
    if (taskId && processingStatus.has(taskId)) {
      res.writeHead(200, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify(processingStatus.get(taskId)))
    } else {
      res.writeHead(404)
      res.end(JSON.stringify({ error: 'Task not found' }))
    }
    return
  }

  // Default: serve static files
  let filePath = path.join(__dirname, req.url === '/' ? 'index.html' : req.url)
  if (fs.existsSync(filePath)) {
    serveFile(res, filePath)
  } else {
    res.writeHead(404)
    res.end('Not found')
  }
})

function serveFile(res, filePath) {
  const ext = path.extname(filePath).toLowerCase()
  const contentType = mimeTypes[ext] || 'application/octet-stream'
  
  fs.readFile(filePath, (err, content) => {
    if (err) {
      res.writeHead(500)
      res.end('Error reading file')
      return
    }
    res.writeHead(200, { 'Content-Type': contentType })
    res.end(content)
  })
}

function handleUpload(req, res) {
  const form = formidable({ uploadDir: UPLOAD_DIR, keepExtensions: true })

  form.parse(req, (err, fields, files) => {
    if (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ error: 'Upload failed' }))
      return
    }

    const fileArray = files.file
    if (!fileArray || !Array.isArray(fileArray) || fileArray.length === 0) {
      res.writeHead(400, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ error: 'No file uploaded' }))
      return
    }

    const file = fileArray[0]
    if (!file || !file.originalFilename) {
      res.writeHead(400, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ error: 'Invalid file' }))
      return
    }

    // Generate unique ID
    const fileId = crypto.randomBytes(8).toString('hex')
    const newFilePath = path.join(UPLOAD_DIR, `${fileId}.npz`)

    // Move file to new location
    fs.renameSync(file.filepath, newFilePath)

    res.writeHead(200, { 'Content-Type': 'application/json' })
    res.end(JSON.stringify({
      success: true,
      filename: `${fileId}.npz`,
      fileId: fileId
    }))
  })
}

function handleProcess(req, res) {
  let body = ''
  req.on('data', chunk => { body += chunk })
  req.on('end', () => {
    try {
      const data = JSON.parse(body)
      const fileId = data.fileId || data.filename.replace('.npz', '')
      const npzFile = path.join(UPLOAD_DIR, `${fileId}.npz`)
      
      if (!fs.existsSync(npzFile)) {
        res.writeHead(404, { 'Content-Type': 'application/json' })
        res.end(JSON.stringify({ error: 'File not found' }))
        return
      }

      const taskId = crypto.randomBytes(8).toString('hex')
      processingStatus.set(taskId, { 
        status: 'processing', 
        progress: 0,
        message: 'Starting conversion...'
      })

      // Run the Python conversion script
      const pythonScript = path.join(__dirname, 'app', 'tapip3d_viz.py')
      const outputBin = path.join(PROCESSED_DIR, `${fileId}.bin`)
      const outputHtml = path.join(PROCESSED_DIR, `${fileId}_viewer.html`)
      
      // Use the venv Python executable (venv is in app folder)
      const pythonExe = process.platform === 'win32' 
        ? path.join(__dirname, 'app', 'venv', 'Scripts', 'python.exe')
        : path.join(__dirname, 'app', 'venv', 'bin', 'python')
      
      const pythonProcess = spawn(pythonExe, [
        pythonScript,
        npzFile,
        '--static-html', outputHtml,
        '-W', '256',
        '-H', '192',
        '-p', '0'  // Don't start server
      ], {
        cwd: path.join(__dirname, 'app')
      })

      let stderr = ''
      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString()
        console.log('Python stderr:', data.toString())
      })

      pythonProcess.stdout.on('data', (data) => {
        console.log('Python stdout:', data.toString())
      })

      pythonProcess.on('close', (code) => {
        if (code === 0) {
          // Read the generated HTML to extract metadata from the embedded data
          fs.readFile(outputHtml, 'utf8', (err, html) => {
            if (err) {
              processingStatus.set(taskId, { status: 'error', message: 'Failed to read output' })
              res.writeHead(500, { 'Content-Type': 'application/json' })
              res.end(JSON.stringify({ error: 'Failed to read output' }))
              return
            }

            // Try to extract metadata by parsing the embedded base64 data
            // For now, just return basic info
            let metadata = {}
            
            // Try to get file size info
            try {
              const stats = fs.statSync(outputBin)
              metadata.fileSize = stats.size
            } catch (e) {}

            processingStatus.set(taskId, { 
              status: 'complete', 
              progress: 100,
              message: 'Ready!',
              metadata: metadata
            })

            res.writeHead(200, { 'Content-Type': 'application/json' })
            res.end(JSON.stringify({ 
              success: true, 
              viewerUrl: `/viewer/${fileId}`,
              metadata: metadata
            }))
          })
        } else {
          processingStatus.set(taskId, { status: 'error', message: stderr || 'Conversion failed' })
          res.writeHead(500, { 'Content-Type': 'application/json' })
          res.end(JSON.stringify({ error: stderr || 'Conversion failed' }))
        }
      })

      // Update progress
      setTimeout(() => {
        if (processingStatus.get(taskId)?.status === 'processing') {
          processingStatus.set(taskId, { 
            status: 'processing', 
            progress: 50,
            message: 'Converting to visualization format...'
          })
        }
      }, 1000)

    } catch (error) {
      res.writeHead(500, { 'Content-Type': 'application/json' })
      res.end(JSON.stringify({ error: error.message }))
    }
  })
}

server.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running at http://localhost:${PORT}`)
})
