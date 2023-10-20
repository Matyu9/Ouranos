from os import system, getcwd, geteuid
from json import dumps
from Utils.database import DataBase
import typer
from InquirerPy import prompt, inquirer
import rich


def default_welcome_message(module):
        print('''  ______     ___      .__   __. .___________. __  .__   __.      ___      
         /      |   /   \     |  \ |  | |           ||  | |  \ |  |     /   \     
        |  ,----'  /  ^  \    |   \|  | `---|  |----`|  | |   \|  |    /  ^  \    
        |  |      /  /_\  \   |  . `  |     |  |     |  | |  . `  |   /  /_\  \   
        |  `----./  _____  \  |  |\   |     |  |     |  | |  |\   |  /  _____  \  
         \______/__/     \__\ |__| \__|     |__|     |__| |__| \__| /__/     \__\ ''')


        print(f"Bienvenue dans l'installateur de Cantina {module} !")

        if geteuid() == 0:
            exit("Le script doit être lancée avec une permission d'administrateur!")

        print('''
        ------------------------------------------------------------------------------------------------------------------------
        ''')


def database_connection():
    db_data = {}

    db_data["username"] = inquirer.text(message="Username of your database :").execute()
    db_data["password"] = inquirer.secret(message="Password of your database :").execute()
    db_data["address"] = inquirer.text(message="Adress/Host of your database :").execute()
    db_data["port"] = inquirer.number(message="Port of your database :").execute()

    database = DataBase(host=db_data["address"], port=str(db_data["port"]), user=db_data["username"],
                        password=db_data['password'])

    try:
        database.connection()
    except ConnectionRefusedError:
        exit('Une erreur est survenue lors de la connexion à MariaDB/MySQL!')

    data = database.select('SHOW DATABASES')

    for db in data:
        if db[0] != 'cantina_administration':
            exit("Merci de d'abord installer l'outils Olympe !")


    print("Une instance de Cantina a été retrouvée dans la base de données. Poursuite de la procédure...")
    print('''
    ------------------------------------------------------------------------------------------------------------------------
    ''')

    return database, db_data


def create_app(database, db_data, module):
    web_address = inquirer.text(message=f"What is the Cantina {module} address (app.example.com) ?")
    custom_path = inquirer.filepath(message=f"Where will be the storage path of  Cantina {module} ? (Enter = {getcwd()}/{module}/)")

    database.insert("""INSERT INTO cantina_administration.domain(name, fqdn) VALUES (%s, %s)""",
                    (f"{module.casefold()}", web_address))

    if custom_path == '':
        custom_path = getcwd()
        print(custom_path)

    system(f"cd {custom_path} && git clone https://github.com/Cantina-Org/{module}.git")

    json_data = {
            "database": [{
                "database_username": db_data["username"],
                "database_password": db_data["password"],
                "database_address": db_data["address"],
                "database_port": db_data["port"]
            }],
            "port": 3002
        }

    with open(custom_path + f'/{module}/config.json', "w") as outfile:
        outfile.write(dumps(json_data, indent=4))

    system(f"""echo '[Unit]
        Description=Cantina {module}
        [Service]
        User=cantina
        WorkingDirectory={custom_path}/{module}
        ExecStart=python3 app.py
        [Install]
        WantedBy=multi-user.target' >> /etc/systemd/system/cantina-{module.casefold()}.service""")

    system(f"chown cantina:cantina {custom_path}/*/*/*")
    system(f"systemctl enable cantina-{module.casefold()}")
    system(f"systemctl start cantina-{module.casefold()}")
