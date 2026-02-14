# 🎙️ Discord 24/7 Voice Channel Bot

A simple yet powerful Discord bot that stays connected to a voice channel **24/7** without interruption. Built with Python and `discord.py`.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![discord.py](https://img.shields.io/badge/discord.py-2.0%2B-5865F2?style=for-the-badge&logo=discord&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

---

## 📋 Table of Contents

- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Bot Setup (Discord Developer Portal)](#-bot-setup-discord-developer-portal)
- [Configuration](#-configuration)
- [Running the Bot](#-running-the-bot)
- [Commands](#-commands)
- [How It Works](#-how-it-works)
- [File Structure](#-file-structure)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔊 **24/7 Voice Connection** | Bot stays in a voice channel around the clock |
| 🔁 **Auto-Reconnect** | Automatically rejoins if disconnected or kicked |
| 🔒 **Move Protection** | Moves back to the correct channel if someone moves it |
| 💾 **Persistent Storage** | Remembers channels across bot restarts |
| ⏱️ **Keep-Alive Loop** | Checks connection every 30 seconds |
| 🌐 **Multi-Server Support** | Works independently in each server |
| 🎨 **Embed Messages** | Beautiful styled embed responses |
| 🔇 **Self-Deafen** | Joins deafened to save bandwidth |
| 🛡️ **Permission System** | Only authorized users can control the bot |
| ⚡ **Slash Commands** | Modern Discord slash command interface |

---

## 📦 Prerequisites

Before you begin, make sure you have:

- **Python 3.8 or higher** — [Download Python](https://www.python.org/downloads/)
- **A Discord Account** — [Create Account](https://discord.com/)
- **A Discord Server** where you have admin permissions

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/discord-247-voice-bot.git
cd discord-247-voice-bot