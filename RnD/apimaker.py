with open("api.txt", "r") as file:
    lines = file.readlines()

processed_lines = [f'"{line.strip()}",\n' for line in lines]

with open("pai.txt", "w") as pia:
    pia.writelines(processed_lines)

print(f"Process selesai!")