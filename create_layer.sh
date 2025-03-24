#!/bin/bash

# Exit script on any error
set -e

echo "🚀 Starting the Lambda Layer Packaging Process..."

# 1. Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
  echo "❌ Error: requirements.txt not found!"
  exit 1
fi

# 2. Create and activate a virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv

echo "✅ Activating virtual environment..."
source venv/bin/activate

# 3. Install dependencies from requirements.txt
echo "📦 Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# 4. Create a directory for Lambda Layer
echo "📁 Creating python directory..."
mkdir -p python

# 5. Install all dependencies into the 'python' directory
echo "📥 Installing dependencies into Lambda Layer..."
pip install --target=python -r requirements.txt

# 6. Zip the layer
echo "🗜️ Zipping the layer..."
zip -r lambda_layer.zip python/

# 7. Cleanup
echo "🧹 Deactivating virtual environment and cleaning up..."
deactivate
rm -rf venv
rm -rf python

echo "✅ Lambda layer packaged successfully: lambda_layer.zip"
