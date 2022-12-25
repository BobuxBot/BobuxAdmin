from dotenv import load_dotenv
from exenenv import EnvironmentProfile


class MainEnvironment(EnvironmentProfile):
    TOKEN: str


load_dotenv()
main = MainEnvironment()
main.load()
