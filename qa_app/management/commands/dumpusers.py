import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Dump users to a file for debugging'

    def handle(self, *args, **options):
        User = get_user_model()
        users = User.objects.all()
        
        output_file = os.path.join('d:\\knowledgebase', 'users_dump.txt')
        with open(output_file, 'w') as f:
            f.write(f"USER MODEL IN USE: {User}\n")
            f.write(f"USERNAME_FIELD: {User.USERNAME_FIELD}\n")
            f.write("-" * 40 + "\n")
            for u in users:
                f.write(f"ID: {u.id}\n")
                f.write(f"  Email: {getattr(u, 'email', 'MISSING')}\n")
                f.write(f"  Username: {getattr(u, 'username', 'MISSING')}\n")
                f.write(f"  Is Staff: {u.is_staff}\n")
                f.write(f"  Is Superuser: {u.is_superuser}\n")
                f.write(f"  Password Hash: {u.password[:20]}...\n")
                f.write("-" * 40 + "\n")
                
        self.stdout.write(self.style.SUCCESS('Users dumped successfully'))
