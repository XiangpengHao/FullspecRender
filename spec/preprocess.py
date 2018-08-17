
def main(filename: str):
    with open(filename) as f:
        all_lines = [float(x) for x in f.readlines()]
    all_lines = all_lines[18:-78]  # from [398, 702]
    rv = []
    for i in range(0, len(all_lines), 5):
        rv.append(sum(all_lines[i:i+5])/5)
    with open(filename.split('.')[0]+'.txt', 'w') as f:
        f.write("\n".join([str(x) for x in rv]))


def color_match():
    filename = 'color_match.csv'
    with open(filename) as f:
        all_lines = [x.split(',')[1:] for x in f.readlines]
    pass


if __name__ == '__main__':
    main('illA_380_780_1.csv')
