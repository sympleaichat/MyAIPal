My AI Pal is a desktop chat client that leverages the power of local large language models (LLMs) to create a personalized AI companion. This application allows you to teach your AI by simply dropping text or PDF files onto it. Your "Pal" learns from these documents and can answer your questions based on the knowledge it has acquired, all while running completely locally on your machine.

The application is built with Python and utilizes a graphical user interface for an interactive and user-friendly experience. It is designed to be a virtual companion that can be customized to your liking, from its name to its appearance.

## Features
Local LLM Integration: My AI Pal uses a local large language model, ensuring your data remains private and secure on your own computer.

Document-Based Learning: Easily teach your AI by dragging and dropping .txt and .pdf files. The AI will process and learn the content of these documents.

Conversational Interface: Engage in natural conversations with your AI. Ask questions, get summaries, and retrieve information from the documents you've provided.

Customizable Appearance: Personalize your AI's name, the user's name, and the overall theme (light/dark modes) of the application. The character's appearance can also be changed by selecting different "character packs."

Conversation History: All interactions are saved in a chat log, which can be reviewed at any time. The AI can also learn from past conversations to improve its responses.

Status Monitoring: A dedicated status window provides insights into what your AI has learned, including the number of documents, total word count, and the size of its knowledge base, visualized with a word cloud.

Proactive Interaction: Your AI companion can initiate conversations if it hasn't been interacted with for a while, creating a more engaging experience.

Cross-Platform Compatibility: The application is designed to run on Windows and is packaged for distribution.

## Technical Overview
My AI Pal is built upon a stack of modern Python libraries to achieve its functionality:

GUI Framework: The user interface is built with customtkinter and tkinterdnd2, providing a modern look and feel with support for drag-and-drop functionality.

AI and Machine Learning: The core AI logic is powered by langchain, which facilitates the interaction with the local LLM. LlamaCpp is used for running the language model, and HuggingFaceEmbeddings with Chroma as a vector store are utilized for creating and querying the knowledge base from your documents.

Packaging: The application is packaged into a standalone executable using tools that handle resource management, making it easy to distribute and run without requiring users to install Python or any dependencies.

## Installation
To run My AI Pal on your local machine, follow these steps:

Prerequisites:

Ensure you have Python 3.8 or higher installed on your system.

You will need a C++ compiler for some of the dependencies. On Windows, Visual Studio with the "Desktop development with C++" workload is recommended.

Clone the Repository:

Bash

git clone https://github.com/your-username/my-ai-pal.git
cd my-ai-pal
Install Dependencies: It is highly recommended to use a virtual environment to manage the project's dependencies.

Bash

python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -r requirements.txt
Download a Local LLM Model: This application requires a GGUF-formatted language model. You can download a model from sources like Hugging Face. Place the downloaded model file into the ./models/ directory. The code is pre-configured to look for tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf.

Run the Application:

Bash

python main.py

## Usage
Once the application is running, you can interact with your AI Pal in the following ways:

Initial Setup: On the first run, you will be prompted to enter your name and a name for your AI.

Teaching Your AI: Drag and drop .txt or .pdf files onto the character's image. A notification will appear indicating that the AI is learning, and another will confirm when the learning process is complete.

Asking Questions: Type your questions into the input box at the bottom and press Enter. The AI will respond based on the documents it has learned from and its general knowledge.

Accessing Features: Use the icon buttons at the bottom to:

Chat Log: View the history of your conversations.

Status: See statistics about the AI's knowledge base.

Settings: Customize the appearance and behavior of the application.

Help: View a quick guide on how to use the application.

Exit: Close the application.

Configuration
The application's settings are stored in a config.json file in the root directory. This file is automatically created and can be modified through the in-app settings menu. The configurable options include:

user_name: Your display name.

ai_name: The name of your AI companion.

theme: The visual theme of the application (light or dark).

character_pack: The folder name of the character assets to be used.

font_face: The font used throughout the application.

font_size: The base font size.

proactive_chat: A boolean to enable or disable the AI's proactive messages.

The prompts used by the LLM can be customized by editing the prompt_config.json file. This allows you to tailor the AI's personality and response style.

## Contributing
Contributions to My AI Pal are welcome! If you have ideas for new features, bug fixes, or improvements, please feel free to:

Fork the repository.

Create a new branch for your feature (git checkout -b feature/AmazingFeature).

Commit your changes (git commit -m 'Add some AmazingFeature').

Push to the branch (git push origin feature/AmazingFeature).

Open a pull request.

Please ensure that your code adheres to the existing style and that you provide clear descriptions of your changes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.

This README provides a comprehensive guide to help you get started with your new AI companion. Enjoy your personalized AI experience!
