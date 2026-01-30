from facefusion.types import Locales

LOCALES : Locales =\
{
	'en':
	{
		'help':
		{
			'model': 'choose the model responsible for restoring the expression',
			'factor': 'restore factor of expression from the target face',
			'areas': 'choose the items used for the expression areas (choices: {choices})'
		},
		'uis':
		{
			'model_dropdown': 'EXPRESSION RESTORER MODEL',
			'factor_slider': 'EXPRESSION RESTORER FACTOR',
			'areas_checkbox_group': 'EXPRESSION RESTORER AREAS'
		}
	},
	'pt':
	{
		'help':
		{
			'model': 'escolha o modelo responsável por restaurar a expressão',
			'factor': 'fator de restauração da expressão da face alvo',
			'areas': 'escolha os itens usados para as áreas de expressão (opções: {choices})'
		},
		'uis':
		{
			'model_dropdown': 'MODELO DO RESTAURADOR DE EXPRESSÃO',
			'factor_slider': 'FATOR DO RESTAURADOR DE EXPRESSÃO',
			'areas_checkbox_group': 'ÁREAS DO RESTAURADOR DE EXPRESSÃO'
		}
	}
}
