MERGE_ENTITIES_PROMPT = """
You are given some entities that may need to be mereged if they are the same.
merge only those that have minor differences like plural form such as SOLDERS and SOLDER or SOLDERING PROCESSES and SOLDERING or acronyms like PCB and PRINTED CIRCUIT BOARD.
Do NOT merge entities that have major differences like SC SOLDERING PROCESSES and CS SOLDERING PROCESSES because they are different processes.
Pay attention to the descriptions of the entities. they have descripe the same thing if discriptions are different merge is not required.
Also only merge thoese that have the same type. if the type is different then don't merge.
Examples:
###
input:
{{'entity': 'PROTECTIVE COATINGS', 'type': 'MATERIAL', 'description': 'Coatings applied to components or the printed circuit board to improve solderability or protect against corrosion.', 'id': 21}},
{{'entity': 'PROTECTIVE COATING', 'type': 'MATERIAL', 'description': 'A protective coating is applied to boards and components to maintain solderability by preventing oxidation of the copper.  However, no coating can maintain solderability indefinitely, and the effectiveness depends on the coating type, storage conditions, and coating thickness.  Re-testing after storage is recommended.>', 'id': 164}}
output:
[{{
    "ids": [21, 164],
    "entities": ["PROTECTIVE COATINGS", "PROTECTIVE COATING"],
    "final_entity": "PROTECTIVE COATINGS",
    "final_description": "Coatings applied to components or the printed circuit board to improve solderability  by preventing oxidation of the copper or protect against corrosion.However, no coating can maintain solderability indefinitely, and the effectiveness depends on the coating type, storage conditions, and coating thickness.  Re-testing after storage is recommended.",
    "final_type": "MATERIAL"
}}]
###
input:
{{'entity': 'CLEANING', 'type': 'PROCESS', 'description': 'Cleaning, in the context of electronics manufacturing, is a crucial process encompassing several stages.  Before soldering, cleaning metallic surfaces ensures proper wetting and a strong solder joint.  After soldering, cleaning removes flux residues and other contaminants from the soldered assemblies, including densely populated printed circuit boards. This post-soldering cleaning step is vital for ensuring the quality, reliability, and longevity of the soldered connections, preventing corrosion and maintaining the integrity of the electronic components.  The choice of cleaning methods and agents is influenced by environmental concerns, necessitating the use of environmentally friendly options where possible.  Cleanliness throughout the entire board manufacturing process, from initial preparation to final assembly, is paramount for optimal performance and reliability.\n', 'id': 11}},
{{'entity': 'CLEANING PROCESSES', 'type': 'PROCESS', 'description': 'Different methods used for cleaning soldered assemblies.', 'id': 59}},
output:
[{{
    "ids": [11, 59],
    "entities": ["CLEANING", "CLEANING PROCESSES"],
    "final_entity": "CLEANING",
    "final_description": "Cleaning, in the context of electronics manufacturing, is a crucial process encompassing several stages.  Before soldering, cleaning metallic surfaces ensures proper wetting and a strong solder joint.  After soldering, cleaning removes flux residues and other contaminants from the soldered assemblies, including densely populated printed circuit boards. This post-soldering cleaning step is vital for ensuring the quality, reliability, and longevity of the soldered connections, preventing corrosion and maintaining the integrity of the electronic components.  The choice of cleaning methods and agents is influenced by environmental concerns, necessitating the use of environmentally friendly options where possible.  Cleanliness throughout the entire board manufacturing process, from initial preparation to final assembly, is paramount for optimal performance and reliability. Different methods used for cleaning soldered assemblies.",
    "final_type": "PROCESS"
}}]
###
input:
{{'entity': 'PCB', 'type': 'MATERIAL', 'description': 'A substrate used in electronics assembly to hold and connect electronic components.  The text mentions PCBs in the context of soldering processes.>', 'id': 4}},
{{'entity': 'PRINTED CIRCUIT BOARD', 'type': 'MATERIAL', 'description': 'A printed circuit board (PCB), also known as a printed wiring board (PWB) or printed board, is a thin board of insulating material serving as a substrate for electronic components.  This substrate is typically made of thermosetting or thermoplastic plastics, often reinforced with materials like paper, glass fiber, cotton, or nylon.  The PCB features conductive pathways, or traces (usually copper), printed on one or both sides, interconnecting components via soldering to lands (pads).  These connections can be made through plated through-holes for leaded components or directly onto the surface for surface-mount components.  PCBs are manufactured using printing techniques, and the conductive tracks can be created additively (adding tracks) or subtractively (removing excess material from a pre-coated base).  They come in single-sided, double-sided, and multi-layered configurations, and are a key element in all electronic assemblies, providing support and pathways for the components mounted and soldered onto them.\n', 'id': 13}},
output:
[{{
    "ids": [4, 13],
    "entities": ["PCB", "PRINTED CIRCUIT BOARD"],
    "final_entity": "PRINTED CIRCUIT BOARD",
    "final_description": "A printed circuit board (PCB), also known as a printed wiring board (PWB) or printed board, is a thin board of insulating material used in electronics assembly to hold and connect electronic components. The PCB serves as a substrate, typically made from thermosetting or thermoplastic plastics, reinforced with materials like paper, glass fiber, cotton, or nylon. It features conductive pathways (usually copper) printed on one or both sides, which interconnect components via soldering to lands (pads). These connections are made either through plated through-holes for leaded components or directly onto the surface for surface-mount components. PCBs are manufactured using printing techniques, and the conductive tracks can be created additively (adding tracks) or subtractively (removing excess material from a pre-coated base). They are available in single-sided, double-sided, and multi-layered configurations, and are essential in all electronic assemblies, providing support and pathways for components during the soldering process.",
    "final_type": "MATERIAL"
}}]
###
input:
{{'entity': 'COMPONENT/SOLDER (CS) PROCESSES', 'type': 'PROCESS', 'description': 'COMPONENT/SOLDER (CS) PROCESSES encompass two main approaches to soldering components onto printed circuit boards.  One method involves placing the component first, followed by the application of solder.  The other method reverses this process, applying solder to the component before placement.  A detailed explanation of various CS soldering processes can be found in a relevant technical book.\n', 'id': 6}},
{{'entity': 'SOLDER/COMPONENT (SC) PROCESSES', 'type': 'PROCESS', 'description': 'SOLDER/COMPONENT (SC) processes encompass several methods used primarily in surface mount assembly production.  These processes involve joining components to a printed circuit board (PCB) using solder.  One common method, often (incorrectly) referred to as reflow, involves applying solder paste (a mixture of solder and flux) to the PCB, placing the components, and then applying heat to melt the solder and create the connection.  Alternatively, solder can be applied to the PCB *before* component placement, or the solder can be applied to the component itself before placement onto the prepared PCB.  The book details various techniques within these broader categories of SC soldering processes.\n', 'id': 7}},
{{'entity': 'HAND SOLDERING', 'type': 'PROCESS', 'description': "Hand soldering is a manual process of soldering components onto a printed circuit board (PCB) individually, using a soldering iron.  This technique, detailed in Chapter 7, is considered a CS soldering process and is typically performed alongside hand assembly, employing specialized tools and techniques specific to the components being soldered.  While offering flexibility for development, prototyping, and rework, hand soldering is slow, laborious, expensive, and its quality is highly dependent on the skill of the operator.  Therefore, it's primarily used in these stages and is cost-ineffective for mass production.\n", 'id': 8}},
{{'entity': 'MASS CS SOLDERING PROCESSES', 'type': 'PROCESS', 'description': 'MASS CS soldering processes are automated processes designed for high-volume, large-scale production.  The processes are described in a book as part of a larger discussion on CS soldering.\n', 'id': 9}},
{{'entity': 'SOLDERING PROCESS', 'type': 'PROCESS', 'description': 'The soldering process is a method of joining materials, typically metallic surfaces such as copper tracks and component leads on printed circuit boards (PCBs), using a filler metal called solder, usually a tin-lead alloy (though modern solders may contain other impurities to modify properties).  This process creates both mechanical and electrical connections, offering a cost-effective and relatively simple joining method.  Soldering involves melting the solder, typically at temperatures around 185°C (though process temperatures can range from 200°C to 350°C depending on the technique), to form metallic bonds between the joined materials.  The process includes several key steps: fluxing (to clean and prepare the surfaces), wetting (ensuring complete solder coverage), heating, and cleaning.  Solderability, the ability of a surface to be completely wetted by the solder, is critical for a successful joint.  Factors such as oxidation and tarnishing can negatively impact solderability, as can the type of flux used; modern trends favor fluxes with minimal reactivity, increasing the importance of clean board preparation.\n\nVarious soldering techniques exist, categorized broadly as component/solder (CS) and solder/component (SC) processes.  CS processes involve placing components before applying solder, while SC processes reverse this order.  Specific techniques include dip soldering, drag soldering, wave soldering, hand soldering, mass soldering, infra-red soldering, hot air convection soldering, hot vapor soldering, laser soldering, and light beam soldering.  The choice of technique depends on factors such as the type of components, the scale of production, and the thermal characteristics of the PCB.  The process can present safety hazards, including burns, electric shocks, and exposure to hazardous materials from the solder and equipment.  The quality of the soldering process is paramount to the functionality and reliability of the resulting electronic assemblies.\n', 'id': 12}},
{{'entity': 'THE SOLDERED JOINT', 'type': 'MATERIAL', 'description': 'The connection formed between components and the printed circuit board using solder.', 'id': 19}},
{{'entity': 'SOLDER PASTE OR ADHESIVE APPLICATION', 'type': 'PROCESS', 'description': 'The process of applying solder paste to the printed circuit board before placing surface mount components.', 'id': 28}},
{{'entity': 'USING SOLDER PASTE', 'type': 'PROCESS', 'description': 'The techniques and procedures involved in using solder paste for surface mount soldering.', 'id': 31}},
{{'entity': 'SOLDER PASTE PARAMETERS', 'type': 'MATERIAL', 'description': 'The properties of solder paste, such as viscosity and particle size, that affect its performance.', 'id': 32}},
{{'entity': 'CS SOLDERING PROCESSES', 'type': 'PROCESS', 'description': 'Soldering processes where the solder is applied to the component before placement on the printed circuit board.', 'id': 33}},
{{'entity': 'SC SOLDERING PROCESSES', 'type': 'PROCESS', 'description': 'Soldering processes where the solder is applied to the printed circuit board before the component is placed.', 'id': 38}},
output:
[
    {{
        "ids": [6, 33],
        "entities": ["COMPONENT/SOLDER (CS) PROCESSES", "CS SOLDERING PROCESSES"],
        "final_entity": "CS PROCESSES",
        "final_description": "COMPONENT/SOLDER (CS) PROCESSES encompass soldering methods where the solder is applied to the component before placement onto the printed circuit board (PCB). This process is used to join components to the PCB, and it can be done in various methods depending on the soldering technique. CS soldering is commonly used in assembly processes and may include both manual and automated techniques.",
        "final_type": "PROCESS"
    }},
    {{
        "ids": [7, 38],
        "entities": ["SOLDER/COMPONENT (SC) PROCESSES", "SC SOLDERING PROCESSES"],
        "final_entity": "SC PROCESSES",
        "final_description": "SOLDER/COMPONENT (SC) PROCESSES refer to soldering techniques where solder is applied to the PCB before the component is placed. These processes are commonly used in surface mount assembly, including reflow soldering, where solder paste (a mixture of solder and flux) is first applied to the PCB, followed by component placement and heating to create electrical connections. Alternative methods involve applying solder to the PCB or the component itself before placement onto the prepared PCB.",
        "final_type": "PROCESS"
    }},
    {{
        "ids": [28, 31],
        "entities": ["SOLDER PASTE OR ADHESIVE APPLICATION", "USING SOLDER PASTE"],
        "final_entity": "SOLDER PASTE APPLICATION",
        "final_description": "SOLDER PASTE APPLICATION refers to the process of applying solder paste to a printed circuit board (PCB) before placing surface mount components. Solder paste, a mixture of solder and flux, is critical in ensuring strong and reliable solder joints in surface mount technology (SMT). The application process can be performed using various techniques, including stencil printing and jet dispensing, depending on the production scale and component density.",
        "final_type": "PROCESS"
    }},
    {{
        "ids": [9, 6],
        "entities": ["MASS CS SOLDERING PROCESSES", "COMPONENT/SOLDER (CS) PROCESSES"],
        "final_entity": "CS SOLDERING PROCESSES",
        "final_description": "MASS COMPONENT/SOLDER (CS) SOLDERING PROCESSES refer to automated, high-volume soldering techniques where solder is applied to the component before it is placed onto the printed circuit board (PCB). These processes are commonly used in large-scale production environments to improve efficiency and consistency in soldering, reducing manual intervention while maintaining quality and reliability.",
        "final_type": "PROCESS"
    }}
]

###
input:
{{'entity': 'SOLDER PASTE PARAMETERS', 'type': 'MATERIAL', 'description': 'The properties of solder paste, such as viscosity and particle size, that affect its performance.', 'id': 32}}
{{'entity': 'CS SOLDERING PROCESSES', 'type': 'PROCESS', 'description': 'Soldering processes where the solder is applied to the component before placement on the printed circuit board.', 'id': 33}}
{{'entity': 'SC SOLDERING PROCESSES', 'type': 'PROCESS', 'description': 'Soldering processes where the solder is applied to the printed circuit board before the component is placed.', 'id': 38}}
output:
[{{
    An Empty List, NO MERGE REQUIRED
}}]
###

input:
{input}
output:
"""

