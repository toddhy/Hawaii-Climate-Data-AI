# Deployment Guide: Remote Access & Nginx Setup

This guide explains how to deploy the HCDP AI Assistant on a remote server using Nginx for production-ready access.

## Current Configuration

### 1. Backend Binding
The backend is configured in `gemini_chat/server.py` to bind to `0.0.0.0:8000`. This allows it to accept connections from any network interface.

### 2. Dynamic Frontend URLs
The frontend source code (`front_end/src/api.ts` and `front_end/src/App.tsx`) has been updated to use dynamic URL resolving:
- **In Development**: Accessing via `localhost:5173` will hit the backend on port `8000`.
- **In Production**: Accessing via Nginx on port `80` will hit the backend via the `/api/` proxy.

### 3. Production Build
The frontend has been built into the `front_end/dist` folder using `npm run build`.

---

## Deployment Steps

### Step 1: Install Nginx
If Nginx is not already installed on the remote server:
```bash
sudo apt update
sudo apt install nginx
```

### Step 2: Configure Nginx
Use the provided `nginx.conf` included in this repository.

1.  Copy the configuration:
    ```bash
    sudo cp nginx.conf /etc/nginx/sites-available/hcdp-app
    ```
2.  Enable the site:
    ```bash
    sudo ln -s /etc/nginx/sites-available/hcdp-app /etc/nginx/sites-enabled/
    ```
3.  Remove the default configuration (optional but recommended):
    ```bash
    sudo rm /etc/nginx/sites-enabled/default
    ```
4.  Test and reload Nginx:
    ```bash
    sudo nginx -t
    sudo systemctl reload nginx
    ```

### Step 3: Serve Frontend Files
Copy the compiled frontend files to the web root:
```bash
sudo mkdir -p /var/www/html
sudo cp -r front_end/dist/* /var/www/html/
```

### Step 4: Run the Backend
Start the backend server on the remote machine:
```bash
python gemini_chat/server.py
```

> [!TIP]
> For production environments, it is highly recommended to use a process manager like **PM2** or a **systemd service** to ensure the backend stays running.

---

## Verification
1. Open your browser and navigate to `http://<SERVER_IP>/`.
2. The HCDP Assistant interface should load.
3. Test a query (e.g., "Map stations near Hilo") to verify that the Nginx proxy is correctly routing API calls to the backend.
