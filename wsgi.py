from app import create_app

app = create_app()

if __name__ == "__main__":
    # TM-07: servidor de desenvolvimento com debug em todas as interfaces
    app.run(host="0.0.0.0", port=8000, debug=True)
