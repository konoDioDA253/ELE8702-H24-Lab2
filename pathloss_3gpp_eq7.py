### Calcul du pathloss avecv les formules 3GPP
# On considere seulement les scenario RMa, UMa et UMi
import math
import sys
infini = float('inf') #définition de l'infini
# Fonction donnant le group et les coords a partir du ID d'un objet dans une liste du meme objet
def get_group_and_coords_by_id_3GPP(object_list, target_id):
    for object in object_list:
        if object.id == target_id:
            return object.group, object.coords
    return None  

# Fonction calculant la distance entre deux point sur le terrain
def calculate_distance_3GPP(coord1, coord2):
    x1, y1 = coord1
    x2, y2 = coord2
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

# Fonction permettant d'afficher un message d'erreur et de stopper le programme
def ERROR_3GPP(msg , code = 1):
    print("\n\n\nERROR\nPROGRAM STOPPED!!!\n")
    if msg:
        print(msg)
    print(f"\n\texit code = {code}\n\n\t\n")
    sys.exit(code)

# Fonction permettant de trouver la valeur d'une cle dans un fichier YAML
def get_from_dict_3GPP(key, data, res=None, curr_level = 1, min_level = 1):
    """Fonction qui retourne la valeur de n'importe quel clé du dictionnaire
       key: clé associé à la valeur recherchée
       data: dictionnaire dans lequel il faut chercher
       les autres sont des paramètres par défaut qu'il ne faut pas toucher"""
    if res:
        return res
    if type(data) is not dict:
        msg = f"get_from_dict_3GPP() works with dicts and is receiving a {type(data)}"
        ERROR_3GPP(msg, 1)
    else:
        # data IS a dictionary
        for k, v in data.items():
            if k == key and curr_level >= min_level:
                #print(f"return data[k] = {data[k]} k = {k}")
                return data[k]
            if type(v) is dict:
                level = curr_level + 1
                res = get_from_dict_3GPP(key, v, res, level, min_level)
    return res 


def check_range(value, range1, range2):
    if value < range1 or value > range2:
        ERROR_3GPP(f"""La valeur {value}m est en dehors de l'intervalle [{range1}, {range2}].
Nous ne pouvons pas appliquer les formules de calcul du pathloss 3GPP.""")








# ************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************
#     RMa LOS ET nlOS
# ************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************

# Cas RMA LOS
def rma_los(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues):
    
    # Definition des fonctions
    def valeur_minimum(val1, val2):
        if val1 < val2:
            val = val1
        if val1 >= val2:
            val = val2
        return val

    def _rma_los_pl1(distance_3D_m, frequence_GHz, hauteur_standard_m):
        min1 = valeur_minimum(0.03*pow(hauteur_standard_m, 1.72), 10)
        min2 = valeur_minimum(0.044*pow(hauteur_standard_m, 1.72), 14.77)
        pl = 20*math.log10(40*math.pi*distance_3D_m*frequence_GHz/3) + min1 - min2 + 0.002*math.log10(hauteur_standard_m)*distance_3D_m
        return pl

    def _rma_los_pl2(distance_3D_m, frequence_GHz, hauteur_standard_m, distance_BP_m):
        pl1 = _rma_los_pl1(distance_BP_m, frequence_GHz, hauteur_standard_m)
        pl = pl1 + 40*math.log10(distance_3D_m/distance_BP_m)
        return pl
    
    # Definition des variables
    c = 3e8
    antenna_group, antenna_coords = get_group_and_coords_by_id_3GPP(antennas, antenna_id)
    ue_group, ue_coords = get_group_and_coords_by_id_3GPP(ues, ue_id)
    distance_2D_m = calculate_distance_3GPP(antenna_coords, ue_coords)
    distance_2D_km = distance_2D_m/1000
    frequence_GHz = get_from_dict_3GPP('frequency', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))
    frequence_Hz = 1000000000*frequence_GHz
    hauteur_BS_m = get_from_dict_3GPP('height', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))
    hauteur_UT_m = get_from_dict_3GPP('height', get_from_dict_3GPP(ue_group,fichier_de_device))
    hauteur_standard_m = 5 # corresponds a la hauteur de batiment moyenne, 5m par defaut



    distance_BP_m = 2* math.pi * hauteur_BS_m * hauteur_UT_m * frequence_Hz / c 
    distance_BP_km = distance_BP_m/1000

    distance_3D_m = math.sqrt(distance_2D_m**2 + (hauteur_BS_m - hauteur_UT_m)**2)
    distance_3D_km = distance_3D_m/1000
    
    # Verifier que nous pouvons utiliser les formules 3GPP avec les valeurs fournies
    check_range(hauteur_BS_m, 10, 150)
    check_range(hauteur_UT_m, 1, 10)
    check_range(hauteur_standard_m, 5, 50)

    # Calcul de pathloss
    warning_message = ""
    if 10 < distance_2D_m and distance_2D_m < distance_BP_m :
        pathloss = _rma_los_pl1(distance_3D_m, frequence_GHz, hauteur_standard_m)
    if distance_BP_km < distance_2D_km and distance_2D_km < 10 :
        pathloss = _rma_los_pl2(distance_3D_m, frequence_GHz, hauteur_standard_m, distance_BP_m)
    if distance_2D_m < 10 :
        warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus petite que 10 m.
Nous considerons un pathloss valant 0 entre ces deux equipements\n"""
        pathloss = 0
    if 10 < distance_2D_km :
        warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus grande que 10 km.
Nous considerons un pathloss valant INFINI entre ces deux equipements\n"""            
        pathloss = infini
    return pathloss, warning_message

# Cas RMA NLOS
def rma_nlos(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues) :
    
    # Definition des fonctions
    def max_comparator(pl_los, pl_nlosp, warning_message_rma_los, warning_message_rma_nlosp):
        if pl_los < pl_nlosp :
            pl = pl_nlosp
            warning_message = warning_message_rma_nlosp
        if pl_los >= pl_nlosp :
            pl = pl_los
            warning_message = warning_message_rma_los
        return pl, warning_message
    
    # Definition des variables
    c = 3e8
    antenna_group, antenna_coords = get_group_and_coords_by_id_3GPP(antennas, antenna_id)
    ue_group, ue_coords = get_group_and_coords_by_id_3GPP(ues, ue_id)
    distance_2D_m = calculate_distance_3GPP(antenna_coords, ue_coords)
    distance_2D_km = distance_2D_m/1000
    frequence_GHz = get_from_dict_3GPP('frequency', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))
    frequence_Hz = 1000000000*frequence_GHz
    hauteur_BS_m = get_from_dict_3GPP('height', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))
    hauteur_UT_m = get_from_dict_3GPP('height', get_from_dict_3GPP(ue_group,fichier_de_device))
    hauteur_standard_m = 5 # corresponds a la hauteur de batiment moyenne, 5m par defaut
    largeur_standard_m = 20 # correspond a la largeur moyenne des rues, 20m par defaut

    distance_BP_m = 2* math.pi * hauteur_BS_m * hauteur_UT_m * frequence_Hz / c 
    distance_BP_km = distance_BP_m/1000

    distance_3D_m = math.sqrt(distance_2D_m**2 + (hauteur_BS_m - hauteur_UT_m)**2)
    distance_3D_km = distance_3D_m/1000
    
    # Verifier que nous pouvons utiliser les formules 3GPP avec les valeurs fournies
    check_range(hauteur_BS_m, 10, 150)
    check_range(hauteur_UT_m, 1, 10)
    check_range(hauteur_standard_m, 5, 50)
    check_range(largeur_standard_m, 5, 50)

    # Calcul de pathloss
    if 10 < distance_2D_m and distance_2D_km < 5 :
        warning_message_rma_los = ""
        warning_message_rma_nlosp = ""
        pl_rma_los, warning_message_rma_los = rma_los(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues)
        pl_rma_nlosp = 161.04 - 7.1*math.log10(largeur_standard_m) + 7.5*math.log10(hauteur_standard_m) - (24.37 - 3.7*(hauteur_standard_m/hauteur_BS_m)**2)*math.log10(hauteur_BS_m) + (43.42 - 3.1*math.log10(hauteur_BS_m))*(math.log10(distance_3D_m) - 3) + 20*math.log10(frequence_GHz) - (3.2*(math.log10(11.75*hauteur_UT_m))**2 - 4.97)
        pathloss, warning_message = max_comparator(pl_rma_los, pl_rma_nlosp, warning_message_rma_los, warning_message_rma_nlosp)
    if distance_2D_m < 10  :
        warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus petite que 10 m.
Nous considerons un pathloss valant 0 entre ces deux equipements\n"""
        pathloss = 0
    if 5 < distance_2D_km :
        warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus grande que 5 km.
Nous considerons un pathloss valant INFINI entre ces deux equipements\n"""            
        pathloss = infini
    return pathloss, warning_message























# ************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************
#     UMa LOS ET nlOS
# ************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************

def uma_los(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues):
    
    # Definition des fonctions
    def _uma_los_pl1(distance_3D_m, frequence_GHz):
        pl = 28.0 + 22*math.log10(distance_3D_m) + 20*math.log10(frequence_GHz)
        return pl

    def _uma_los_pl2(distance_3D_m, frequence_GHz, distance_prime_BP_m, hauteur_BS_m, hauteur_UT_m):
        pl = 28.0 + 40*math.log10(distance_3D_m) + 20*math.log10(frequence_GHz) - 9*math.log10(distance_prime_BP_m**2 + (hauteur_BS_m - hauteur_UT_m)**2) 
        return pl
    
    # Definition des variables
    c = 3e8
    antenna_group, antenna_coords = get_group_and_coords_by_id_3GPP(antennas, antenna_id)
    ue_group, ue_coords = get_group_and_coords_by_id_3GPP(ues, ue_id)
    distance_2D_m = calculate_distance_3GPP(antenna_coords, ue_coords)
    distance_2D_km = distance_2D_m/1000
    frequence_GHz = get_from_dict_3GPP('frequency', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))
    frequence_Hz = 1000000000*frequence_GHz
    hauteur_BS_m = get_from_dict_3GPP('height', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))
    hauteur_UT_m = get_from_dict_3GPP('height', get_from_dict_3GPP(ue_group,fichier_de_device))

    hE_m = 1.0 
    hauteur_prime_BS_m = hauteur_BS_m - hE_m 
    hauteur_prime_UT_m = hauteur_UT_m - hE_m 

    distance_prime_BP_m = 4 * hauteur_prime_BS_m * hauteur_prime_UT_m * frequence_Hz / c 
    distance_prime_BP_km = distance_prime_BP_m/1000

    # distance_BP_m = 4 * hauteur_BS_m * hauteur_UT_m * frequence_Hz / c 
    # distance_BP_km = distance_BP_m/1000

    distance_3D_m = math.sqrt(distance_2D_m**2 + (hauteur_BS_m - hauteur_UT_m)**2)
    distance_3D_km = distance_3D_m/1000

    # Verifier que nous pouvons utiliser les formules 3GPP avec les valeurs fournies
    check_range(hauteur_UT_m, 1.5, 22.5)

    # Calcul de pathloss
    warning_message = ""
    if 10 < distance_2D_m and distance_2D_m < distance_prime_BP_m :
        pathloss = _uma_los_pl1(distance_3D_m, frequence_GHz)
    if distance_prime_BP_km < distance_2D_km and distance_2D_km < 5 :
        pathloss = _uma_los_pl2(distance_3D_m, frequence_GHz, distance_prime_BP_m, hauteur_BS_m, hauteur_UT_m)
    if distance_2D_m < 10 :
            warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus petite que 10 m.
Nous considerons un pathloss valant 0 entre ces deux equipements\n"""
            pathloss = 0
    if 5 < distance_2D_km :
            warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus grande que 5 km.
Nous considerons un pathloss valant INFINI entre ces deux equipements\n"""            
            pathloss = infini
    return pathloss, warning_message

def uma_nlos(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues) :
    
    # Definition des fonctions
    def max_comparator(pl_los, pl_nlosp, warning_message_uma_los, warning_message_uma_nlosp):
        if pl_los < pl_nlosp :
            pl = pl_nlosp
            warning_message = warning_message_uma_nlosp
        if pl_los >= pl_nlosp :
            pl = pl_los
            warning_message = warning_message_uma_los
        return pl, warning_message
    
    # Definition des variables
    c = 3e8
    antenna_group, antenna_coords = get_group_and_coords_by_id_3GPP(antennas, antenna_id)
    ue_group, ue_coords = get_group_and_coords_by_id_3GPP(ues, ue_id)
    distance_2D_m = calculate_distance_3GPP(antenna_coords, ue_coords)
    distance_2D_km = distance_2D_m/1000
    frequence_GHz = get_from_dict_3GPP('frequency', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))
    frequence_Hz = 1000000000*frequence_GHz
    hauteur_BS_m = get_from_dict_3GPP('height', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))
    hauteur_UT_m = get_from_dict_3GPP('height', get_from_dict_3GPP(ue_group,fichier_de_device))

    hE_m = 1.0 
    hauteur_prime_BS_m = hauteur_BS_m - hE_m 
    hauteur_prime_UT_m = hauteur_UT_m - hE_m 

    distance_prime_BP_m = 4 * hauteur_prime_BS_m * hauteur_prime_UT_m * frequence_Hz / c 
    distance_prime_BP_km = distance_prime_BP_m/1000

    # distance_BP_m = 4 * hauteur_BS_m * hauteur_UT_m * frequence_Hz / c 
    # distance_BP_km = distance_BP_m/1000

    distance_3D_m = math.sqrt(distance_2D_m**2 + (hauteur_BS_m - hauteur_UT_m)**2)
    distance_3D_km = distance_3D_m/1000
    
    
    # Verifier que nous pouvons utiliser les formules 3GPP avec les valeurs fournies
    check_range(hauteur_UT_m, 1.5, 22.5)

    # Calcul de pathloss
    if 10 < distance_2D_m and distance_2D_km < 5 :
        warning_message_uma_los = ""
        warning_message_uma_nlosp = ""
        pl_uma_los, warning_message_uma_los = uma_los(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues)
        pl_uma_nlosp = 13.54 + 39.08*math.log10(distance_3D_m) + 20*math.log10(frequence_GHz) -0.6*(hauteur_UT_m - 1.5)
        pathloss, warning_message = max_comparator(pl_uma_los, pl_uma_nlosp, warning_message_uma_los, warning_message_uma_nlosp)
    if distance_2D_m < 10  :
            warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus petite que 10 m.
Nous considerons un pathloss valant 0 entre ces deux equipements\n"""
            pathloss = 0
    if 5 < distance_2D_km :
            warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus grande que 5 km.
Nous considerons un pathloss valant INFINI entre ces deux equipements\n"""            
            pathloss = infini
    return pathloss, warning_message






























# ************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************
#     UMi LOS ET nlOS
# ************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************

def umi_los(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues):
    
    # Definition des fonctions
    def _umi_los_pl1(distance_3D_m, frequence_GHz):
        pl = 32.4 + 21*math.log10(distance_3D_m) + 20*math.log10(frequence_GHz)
        return pl

    def _umi_los_pl2(distance_3D_m, frequence_GHz, distance_BP_m, hauteur_BS_m, hauteur_UT_m):
        pl = 32.4 + 40*math.log10(distance_3D_m) + 20*math.log10(frequence_GHz) - 9.5*math.log10(distance_BP_m**2 + (hauteur_BS_m - hauteur_UT_m)**2) 
        return pl
    
    # Definition des variables
    c = 3e8
    antenna_group, antenna_coords = get_group_and_coords_by_id_3GPP(antennas, antenna_id)
    ue_group, ue_coords = get_group_and_coords_by_id_3GPP(ues, ue_id)
    distance_2D_m = calculate_distance_3GPP(antenna_coords, ue_coords)
    distance_2D_km = distance_2D_m/1000
    frequence_GHz = get_from_dict_3GPP('frequency', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))
    frequence_Hz = 1000000000*frequence_GHz
    hauteur_BS_m = get_from_dict_3GPP('height', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))
    hauteur_UT_m = get_from_dict_3GPP('height', get_from_dict_3GPP(ue_group,fichier_de_device))
    hE_m = 1.0 
    hauteur_prime_BS_m = hauteur_BS_m - hE_m 
    hauteur_prime_UT_m = hauteur_UT_m - hE_m 

    distance_prime_BP_m = 4 * hauteur_prime_BS_m * hauteur_prime_UT_m * frequence_Hz / c 
    distance_prime_BP_km = distance_prime_BP_m/1000

    distance_3D_m = math.sqrt(distance_2D_m**2 + (hauteur_BS_m - hauteur_UT_m)**2)
    distance_3D_km = distance_3D_m/1000

    # Verifier que nous pouvons utiliser les formules 3GPP avec les valeurs fournies
    check_range(hauteur_UT_m, 1.5, 22.5)

    # Calcul de pathloss
    warning_message = ""
    if 10 < distance_2D_m and distance_2D_m < distance_prime_BP_m :
        pathloss = _umi_los_pl1(distance_3D_m, frequence_GHz)
    if distance_prime_BP_m < distance_2D_m and distance_2D_km < 5 :
        pathloss = _umi_los_pl2(distance_3D_m, frequence_GHz, distance_prime_BP_m, hauteur_BS_m, hauteur_UT_m)
    if distance_2D_m < 10 :
            warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus petite que 10 m.
Nous considerons un pathloss valant 0 entre ces deux equipements\n"""
            pathloss = 0
    if 5 < distance_2D_km :
            warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus grande que 5 km.
Nous considerons un pathloss valant INFINI entre ces deux equipements\n"""            
            pathloss = infini
    return pathloss, warning_message

def umi_nlos(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues) :
    
    # Definition des fonctions
    def max_comparator(pl_los, pl_nlosp, warning_message_umi_los, warning_message_umi_nlosp):
        if pl_los < pl_nlosp :
            pl = pl_nlosp
            warning_message = warning_message_umi_nlosp
        if pl_los >= pl_nlosp :
            pl = pl_los
            warning_message = warning_message_umi_los
        return pl, warning_message
    
    # Definition des variables
    c = 3e8
    antenna_group, antenna_coords = get_group_and_coords_by_id_3GPP(antennas, antenna_id)
    ue_group, ue_coords = get_group_and_coords_by_id_3GPP(ues, ue_id)
    distance_2D_m = calculate_distance_3GPP(antenna_coords, ue_coords)
    distance_2D_km = distance_2D_m/1000
    frequence_GHz = get_from_dict_3GPP('frequency', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))
    frequence_Hz = 1000000000*frequence_GHz
    hauteur_BS_m = get_from_dict_3GPP('height', get_from_dict_3GPP(antenna_group, get_from_dict_3GPP(next(iter(fichier_de_device)), fichier_de_device)))
    hauteur_UT_m = get_from_dict_3GPP('height', get_from_dict_3GPP(ue_group,fichier_de_device))

    hE_m = 1.0 
    hauteur_prime_BS_m = hauteur_BS_m - hE_m 
    hauteur_prime_UT_m = hauteur_UT_m - hE_m 

    distance_prime_BP_m = 4 * hauteur_prime_BS_m * hauteur_prime_UT_m * frequence_Hz / c 
    distance_prime_BP_km = distance_prime_BP_m/1000

    distance_3D_m = math.sqrt(distance_2D_m**2 + (hauteur_BS_m - hauteur_UT_m)**2)
    distance_3D_km = distance_3D_m/1000
    
    # Verifier que nous pouvons utiliser les formules 3GPP avec les valeurs fournies
    check_range(hauteur_UT_m, 1.5, 22.5)
    
    # Calcul de pathloss
    if 10 < distance_2D_m and distance_2D_km < 5 :
        warning_message_umi_los = ""
        warning_message_umi_nlosp = ""
        pl_umi_los, warning_message_umi_los = umi_los(fichier_de_cas, fichier_de_device, antenna_id, ue_id, antennas, ues)
        pl_umi_nlosp = 35.3*math.log10(distance_3D_m) + 22.4 + 21.3*math.log10(frequence_GHz) - 0.3*(hauteur_UT_m - 1.5)
        pathloss, warning_message = max_comparator(pl_umi_los, pl_umi_nlosp, warning_message_umi_los, warning_message_umi_nlosp)
    if distance_2D_m < 10  :
            warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus petite que 10 m.
Nous considerons un pathloss valant 0 entre ces deux equipements\n"""
            pathloss = 0
    if  5 < distance_2D_km :
            warning_message = f"""WARNING : la distance entre l'UE {ue_id} et l'antenne {antenna_id} est plus grande que 5 km.
Nous considerons un pathloss valant INFINI entre ces deux equipements\n"""            
            pathloss = infini
    return pathloss, warning_message