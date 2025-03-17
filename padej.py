from pytrovich.enums import NamePart, Gender, Case
from pytrovich.maker import PetrovichDeclinationMaker

maker = PetrovichDeclinationMaker()
print(maker.make(NamePart.LASTNAME, Gender.MALE, Case.ACCUSATIVE, "Мустафин"))  # Винительный 
print(maker.make(NamePart.LASTNAME, Gender.MALE, Case.DATIVE, "Мустафин"))  # Дательный
print(maker.make(NamePart.LASTNAME, Gender.MALE, Case.GENITIVE, "Мустафин"))  # Родительный 
print(maker.make(NamePart.LASTNAME, Gender.MALE, Case.INSTRUMENTAL, "Мустафин"))  # Творительный
print(maker.make(NamePart.LASTNAME, Gender.MALE, Case.PREPOSITIONAL, "Мустафин"))  # Предложный

