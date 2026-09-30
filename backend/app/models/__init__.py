# models package — import all so SQLAlchemy registers them
from app.models.user import User
from app.models.scheme import Scheme
from app.models.document import DocumentAnalysis
from app.models.interaction import ItemInteraction, AdaptiveWeight
