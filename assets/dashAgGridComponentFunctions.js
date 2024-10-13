var dagfuncs = (window.dashAgGridFunctions = window.dashAgGridFunctions || {});

// this is to format the number in the cell
dagfuncs.numberFormatter = function(value) {
    if (value === null || value === undefined) {
        return '';
    }
    const formattedValue = Math.abs(value).toLocaleString('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
    });
    return value < 0 ? `(${formattedValue})` : formattedValue;
};

// this is to highlight the row and column of the cell
dagfuncs.HighlightCellRenderer = function (props) {
    const [backgroundColor, setBackgroundColor] = React.useState('');
    
    React.useEffect(() => {
        const getColumnCells = (field) => {
            return [
                ...document.querySelectorAll(`.ag-pinned-left-cols-container .ag-cell[col-id='${field}']`),
                ...document.querySelectorAll(`.ag-center-cols-container .ag-cell[col-id='${field}']`)
            ];
        };

        const getRowCells = (parentElement) => {
            return [
                ...parentElement.childNodes,
                ...document.querySelectorAll(`.ag-pinned-left-cols-container .ag-row[row-index='${props.node.rowIndex}'] .ag-cell`)
            ];
        };

        const columnCells = getColumnCells(props.colDef.field);
        const rowCells = getRowCells(props.eGridCell.parentElement);

        const onMouseOver = () => {
            columnCells.forEach(cell => cell.classList.add('highlight-column'));
            rowCells.forEach(cell => cell.classList.add('highlight-row'));
        };

        const onMouseOut = () => {
            columnCells.forEach(cell => cell.classList.remove('highlight-column'));
            rowCells.forEach(cell => cell.classList.remove('highlight-row'));
        };

        const cellElement = props.eGridCell;
        cellElement.addEventListener('mouseover', onMouseOver);
        cellElement.addEventListener('mouseout', onMouseOut);

        return () => {
            cellElement.removeEventListener('mouseover', onMouseOver);
            cellElement.removeEventListener('mouseout', onMouseOut);
        };
    }, [props.eGridCell, props.colDef.field, props.node.rowIndex]);

    return React.createElement(
        'div',
        { style: { backgroundColor: backgroundColor } },
        props.value
    );
};
