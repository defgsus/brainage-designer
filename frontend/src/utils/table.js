
export function table_string_sorter(dataIndex) {
    return (a, b) => {
        a = a[dataIndex];
        b = b[dataIndex];
        if (!a)
            return 1;
        if (!b)
            return -1;

        if (a.toLowerCase)
            a = a.toLowerCase();
        if (b.toLowerCase)
            b = b.toLowerCase();

        return a < b ? -1 : a === b ? 0 : 1;
    };
}

export function table_number_sorter(dataIndex) {
    return (a, b) => {
        a = a[dataIndex];
        b = b[dataIndex];
        if (typeof a !== "number")
            return 1;
        if (typeof b !== "number")
            return -1;
        return a < b ? -1 : 1;
    };
}

export function table_date_sorter(dataIndex) {
    return table_string_sorter(dataIndex);
}
