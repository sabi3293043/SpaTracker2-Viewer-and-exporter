module.exports = {
  daemon: true,
  run: [
    {
      method: "shell.run",
      params: {
        path: "app",
        venv: "venv",
        chain: true,
        env: {},
        input: null,
        message: [
          "python -m http.server {{port}}",
        ],
        on: [
          {
            event: "/Serving HTTP on/",
            done: true
          }
        ]
      }
    },
    {
      when: "{{input && input.event && Array.isArray(input.event) && input.event.length > 0}}",
      method: "local.set",
      params: {
        url: "http://localhost:{{port}}/viewer.html"
      }
    }
  ]
}
