import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection

# 1. Definiere Koordinaten der Knoten gemäß dem Beispiel
nodes = np.array([
    [0, 0],  # Knoten 1
    [1, 0],  # Knoten 2
    [2, 0],  # Knoten 3
    [2, 1],  # Knoten 4
    [1, 1],  # Knoten 5
    [0, 1]   # Knoten 6
])

# 2. Definiere Elemente durch ihre Knoten
elements = np.array([
    [0, 1, 4],  # Element 1: Knoten 1, 2, 5
    [1, 2, 3],  # Element 2: Knoten 2, 3, 4
    [3, 4, 1],  # Element 3: Knoten 4, 5, 2
    [4, 5, 0]   # Element 4: Knoten 5, 6, 1
])

# 3. Materialparameter (aus dem Beispiel)
# D-Matrix für ebenen Verzerrungszustand
D = np.array([
    [1.0, 0.5, 0.0],
    [0.5, 1.0, 0.0],
    [0.0, 0.0, 1.0]
])

# 4. Erstelle globale Steifigkeitsmatrix
num_nodes = len(nodes)
K_global = np.zeros((2*num_nodes, 2*num_nodes))  # 2 DOF pro Knoten (u, v)

# 5. Berechnung der Element-Steifigkeitsmatrizen und Assemblierung
for el_idx, element in enumerate(elements):
    # Extrahiere Knotenkoordinaten für das aktuelle Element
    node1, node2, node3 = element
    x1, y1 = nodes[node1]
    x2, y2 = nodes[node2]
    x3, y3 = nodes[node3]
    
    # Berechne Fläche des Elements
    area = 0.5 * abs((x2-x1)*(y3-y1) - (x3-x1)*(y2-y1))
    
    # Koeffizienten für B-Matrix
    b1 = (y2 - y3) / (2 * area)
    b2 = (y3 - y1) / (2 * area)
    b3 = (y1 - y2) / (2 * area)
    c1 = (x3 - x2) / (2 * area)
    c2 = (x1 - x3) / (2 * area)
    c3 = (x2 - x1) / (2 * area)
    
    # Erstelle B-Matrix
    B = np.array([
        [b1, 0, b2, 0, b3, 0],
        [0, c1, 0, c2, 0, c3],
        [c1, b1, c2, b2, c3, b3]
    ])
    
    # Berechne Element-Steifigkeitsmatrix K_el = B^T * D * B * Fläche
    K_el = area * np.dot(np.dot(B.T, D), B)
    
    # Assembliere in globale Steifigkeitsmatrix
    for i in range(3):  # 3 Knoten pro Element
        for j in range(3):  # 3 Knoten pro Element
            # Globale Indizes für Knoten i und j
            n_i = element[i]
            n_j = element[j]
            
            # Füge Beiträge zur globalen Steifigkeitsmatrix hinzu
            # Für jeden Knoten gibt es 2 DOF (u und v)
            K_global[2*n_i, 2*n_j] += K_el[2*i, 2*j]         # uu
            K_global[2*n_i, 2*n_j+1] += K_el[2*i, 2*j+1]     # uv
            K_global[2*n_i+1, 2*n_j] += K_el[2*i+1, 2*j]     # vu
            K_global[2*n_i+1, 2*n_j+1] += K_el[2*i+1, 2*j+1] # vv

# 6. Anwenden der Randbedingungen
# Fixierte Knoten: 1 und 6 (Indizes 0 und 5)
fixed_dofs = [0, 1, 10, 11]  # 2*0, 2*0+1, 2*5, 2*5+1

# Kraft auf Knoten 4 (Index 3) in negative y-Richtung
force_vector = np.zeros(2*num_nodes)
force_vector[7] = -1  # 2*3+1 (v-Komponente von Knoten 4)

# 7. Modifiziere das System für die bekannten Verschiebungswerte
# Entferne Zeilen und Spalten für fixierte DOFs
free_dofs = [i for i in range(2*num_nodes) if i not in fixed_dofs]
K_reduced = K_global[np.ix_(free_dofs, free_dofs)]
f_reduced = force_vector[free_dofs]

# 8. Löse das System
u_reduced = np.linalg.solve(K_reduced, f_reduced)

# 9. Rekonstruiere vollen Verschiebungsvektor
u_full = np.zeros(2*num_nodes)
for i, dof in enumerate(free_dofs):
    u_full[dof] = u_reduced[i]

# 10. Extrahiere Verschiebungen für jeden Knoten
displacements = []
for i in range(num_nodes):
    displacements.append([u_full[2*i], u_full[2*i+1]])
displacements = np.array(displacements)

# 11. Berechnung der Spannungen für jedes Element
stresses = []
for el_idx, element in enumerate(elements):
    # Extrahiere Knotenkoordinaten
    node1, node2, node3 = element
    x1, y1 = nodes[node1]
    x2, y2 = nodes[node2]
    x3, y3 = nodes[node3]
    
    # Berechne Fläche des Elements
    area = 0.5 * abs((x2-x1)*(y3-y1) - (x3-x1)*(y2-y1))
    
    # Koeffizienten für B-Matrix
    b1 = (y2 - y3) / (2 * area)
    b2 = (y3 - y1) / (2 * area)
    b3 = (y1 - y2) / (2 * area)
    c1 = (x3 - x2) / (2 * area)
    c2 = (x1 - x3) / (2 * area)
    c3 = (x2 - x1) / (2 * area)
    
    # Erstelle B-Matrix
    B = np.array([
        [b1, 0, b2, 0, b3, 0],
        [0, c1, 0, c2, 0, c3],
        [c1, b1, c2, b2, c3, b3]
    ])
    
    # Extrahiere Elementverschiebungen
    u_element = np.array([
        u_full[2*node1], u_full[2*node1+1],
        u_full[2*node2], u_full[2*node2+1],
        u_full[2*node3], u_full[2*node3+1]
    ])
    
    # Berechne Dehnungen
    strain = np.dot(B, u_element)
    
    # Berechne Spannungen
    stress = np.dot(D, strain)
    stresses.append(stress)

# Gib berechnete Werte aus
print("Verschiebungen (u, v):")
for i, disp in enumerate(displacements):
    print(f"Knoten {i+1}: ({disp[0]:.4f}, {disp[1]:.4f})")

print("\nSpannungen (sigma_x, sigma_y, tau_xy):")
for i, stress in enumerate(stresses):
    print(f"Element {i+1}: ({stress[0]:.4f}, {stress[1]:.4f}, {stress[2]:.4f})")

# Berechne von Mises Spannungen
von_mises = []
for stress in stresses:
    # Von Mises Spannung für 2D: sqrt(sigma_x^2 - sigma_x*sigma_y + sigma_y^2 + 3*tau_xy^2)
    sigma_x = stress[0]
    sigma_y = stress[1]
    tau_xy = stress[2]
    vm = np.sqrt(sigma_x**2 - sigma_x*sigma_y + sigma_y**2 + 3*tau_xy**2)
    von_mises.append(vm)

print("\nVon Mises Spannungen:")
for i, vm in enumerate(von_mises):
    print(f"Element {i+1}: {vm:.4f}")

# 12. Visualisiere Ergebnisse - ANGEPASST
plt.figure(figsize=(14, 6))

# Plot originale und deformierte Struktur
plt.subplot(121)
plt.title("Original (blau) und deformierte Struktur (rot)")

# Skalierungsfaktor für bessere Sichtbarkeit der Verschiebungen
# Reduziert für realistischere Darstellung
scale = 0.05

# Zeichne original und deformiert
for el in elements:
    # Original
    polygon = Polygon(nodes[el], fill=False, edgecolor='blue')
    plt.gca().add_patch(polygon)
    
    # Deformiert
    deformed_nodes = nodes + scale * displacements
    polygon = Polygon(deformed_nodes[el], fill=False, edgecolor='red')
    plt.gca().add_patch(polygon)

# Zeichne Knoten mit Beschriftung
plt.scatter(nodes[:, 0], nodes[:, 1], c='blue', s=50, label='Original')
plt.scatter(nodes[:, 0] + scale * displacements[:, 0], 
            nodes[:, 1] + scale * displacements[:, 1], 
            c='red', s=50, label='Deformiert')

# Beschrifte Knoten
for i in range(len(nodes)):
    plt.text(nodes[i, 0], nodes[i, 1], str(i+1), fontsize=12)

# Setze die Achsengrenzen explizit für bessere Darstellung
plt.xlim(-0.5, 2.5)
plt.ylim(-0.5, 1.5)
plt.axis('equal')
plt.grid(True)
plt.legend()

# Plotte von Mises Spannungen
plt.subplot(122)
plt.title("Von Mises Spannungen")

# Erstelle Farbkarte für Elemente
patches = []
for i, el in enumerate(elements):
    polygon = Polygon(nodes[el], fill=True)
    patches.append(polygon)

p = PatchCollection(patches, cmap='jet', alpha=0.7)
p.set_array(np.array(von_mises))
plt.gca().add_collection(p)
plt.colorbar(p, label='Von Mises Spannung')

plt.xlim(-0.1, 2.1)
plt.ylim(-0.1, 1.1)
plt.axis('equal')
plt.grid(True)

plt.tight_layout()
plt.savefig('fem_result.png', dpi=300)  # Speichert die Abbildung in hoher Qualität
plt.show()

# Zusätzlich: Reaktionskräfte an den fixierten Knoten berechnen
reaction_forces = np.dot(K_global, u_full) - force_vector
print("\nReaktionskräfte (fx, fy):")
print(f"Knoten 1: ({reaction_forces[0]:.4f}, {reaction_forces[1]:.4f})")
print(f"Knoten 6: ({reaction_forces[10]:.4f}, {reaction_forces[11]:.4f})")