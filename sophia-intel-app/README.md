# Sophia Intel App UI

The business intelligence dashboard for PayReady's Sophia Intel platform. Built with Next.js, Tailwind CSS, and TypeScript for enterprise BI and analytics.

<img src="https://github.com/user-attachments/assets/7765fae5-a813-46cb-993b-904af9bc1672" alt="sophia-intel-app" style="border-radius: 10px; width: 100%; max-width: 800px;" />

## Features

- 💬 **Modern Chat Interface**: Clean design with real-time streaming support
- 🧩 **Tool Calls Support**: Visualizes agent tool calls and their results
- 🧠 **Reasoning Steps**: Displays agent reasoning process (when available)
- 📚 **References Support**: Show sources used by the agent
- 🖼️ **Multi-modality Support**: Handles various content types including images, video, and audio
- 🎨 **Customizable UI**: Built with Tailwind CSS for easy styling
- 🧰 **Built with Modern Stack**: Next.js, TypeScript, shadcn/ui, Framer Motion, and more

## Getting Started

### Prerequisites

Before setting up Sophia Intel App, ensure the Sophia API backend is running on port 8003. This connects to integrated business systems like Salesforce, Slack, HubSpot, and Gong.

### Installation

### Automatic Installation (Recommended)

```bash
npx create-sophia-intel-app@latest
```

### Manual Installation

1. Clone the repository:

```bash
# This is the Sophia Intel App UI - part of the unified business intelligence platform
cd sophia-intel-app
```

2. Install dependencies:

```bash
pnpm install
```

3. Start the development server:

```bash
pnpm dev
```

4. Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Connecting to an Agent Backend

By default Agent UI connects to `http://localhost:7777`. You can easily change this by hovering over the endpoint URL and clicking the edit option.

The default endpoint connects to the Sophia API backend at http://localhost:8003 for business intelligence operations.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for contribution guidelines.

## License

This project is licensed under the [MIT License](./LICENSE).
