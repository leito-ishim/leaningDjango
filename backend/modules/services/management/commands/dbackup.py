from django.core.management import call_command, BaseCommand
from datetime import datetime

class Command(BaseCommand):
    """
    Команда для создания резервной копии базы данных
    """

    def handle(self, *args, **options):
        self.stdout.write('Waitining for database dump...')
        call_command(
            'dumpdata',
            '--natural-foreign',
            '--natural-primary',
            '--exclude=contenttypes',
            '--exclude=admin.logentry',
            '--indent=4',
            f'--output=database-{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.json'
        )
        self.stdout.write(self.style.SUCCESS('Database successfully backed up'))
