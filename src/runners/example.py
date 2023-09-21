import shutil

from .template import Runner, RunnerInfo

# vytvor triedu (pomenuj lubovolne, ale odvod ju od Runner)
class ExampleRunner(Runner):
	# info o tomto jazyku: nazov, pripony, ci sa musi kompilovat
	# pokial sa nemusi kompilovat, vynechaj aj prepare_compile a compile
	info = RunnerInfo('Example language', ['exa', 'example'], True)

	# toto sa spusti pred kompilaciou
	# box_path je priecinok, v ktorom pracujeme
	# source_path je nazov suboru odovzdaneho pouzivatelom (uz sa nachadza v priecinku)
	# v podstate tu by sme mali odkopirovat vsetko, co potrebujeme
	@staticmethod
	def prepare_compile(box_path: str, source_path: str):
		shutil.copy('/usr/bin/my_compiler', box_path)


	# vystup tohto prikazu vidi pouzivatel ako chybu, pokial prikaz skonci chybou
	# tato funkcia ma vratit list so stringami, teda s prikazom, ktory sa ma spustit
	# POZOR: tento prikaz nebezi v izolovanom prostredii
	@staticmethod
	def compile(box_path: str, file: str) -> list[str]:
		return ['my_compiler', '-parameter', '-iny parameter', file]

	# ako prepare_compile, ale pred spustenim programu
	@staticmethod
	def prepare_runtime(box_path: str):
		shutil.copy('/usr/bin/my_runner', box_path)

	# ako compile, ale prikaz programu, ktory sa ma spustit
	# na vstup dostane vstup a vystup (stdout) sa potom ulozi do suboru, ktory sa ohodnoti
	@staticmethod
	def run(file: str) -> list[str]:
		return ['my_runner', file]

# tu returni tebou vytvorenu triedu
# tu sa tiez moze nachadzat nejaka pridana logika pre overenie prostredia, stiahnutie potrebnych suboro a podobne
def init():
	return ExampleRunner