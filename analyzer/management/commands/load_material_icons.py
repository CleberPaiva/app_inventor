from django.core.management.base import BaseCommand
from analyzer.utils import load_material_icons


class Command(BaseCommand):
    help = 'Carrega os ícones do Material Design da biblioteca local'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force-reload',
            action='store_true',
            help='Força o recarregamento mesmo se o cache existir',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Iniciando carregamento dos ícones do Material Design...')
        )
        
        try:
            # Carrega os ícones
            load_material_icons()
            
            self.stdout.write(
                self.style.SUCCESS('✅ Ícones do Material Design carregados com sucesso!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro ao carregar ícones: {str(e)}')
            )
            raise e
