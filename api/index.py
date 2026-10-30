from app import create_app
from app.vercel_routing import OriginalPathMiddleware

app = create_app()
app.wsgi_app = OriginalPathMiddleware(app.wsgi_app)
