const http = require('http')
const fs = require('fs')
const path = require('path')
const formidable = require('formidable')
const { spawn } = require('child_process')

module.exports = {
  daemon: true,
  run: [
    {
      method: "shell.run",
      params: {
        venv: "venv",
        path: ".",
        env: {},
        message: `node viewer_server.js {{port}}`,
        on: [
          {
            event: "/Server running at (http[s]?://[0-9a-zA-Z.:]+)/",
            done: true
          }
        ]
      }
    },
    {
      method: "local.set",
      params: {
        url: "{{input.event[1]}}"
      }
    }
  ]
}
