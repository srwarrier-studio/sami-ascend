export type BoardWidget = { id: string; catalogId: string }
export type Board = { id: string; name: string; widgets: BoardWidget[] }

export type BoardStore = {
  list: () => Promise<Board[]>
  create: (name: string) => Promise<Board>
  rename: (id: string, name: string) => Promise<void>
  remove: (id: string) => Promise<void>
  saveWidgets: (id: string, widgets: BoardWidget[]) => Promise<void>
}

const seed = (): Board[] => [
  {
    id: 'board-1',
    name: 'Sales overview',
    widgets: ['sales-today', 'sales-month', 'sales-year', 'orders-month', 'month-on-month', 'day-sales', 'status-split', 'top-customers', 'top-materials', 'high-value-sales'].map(
      (catalogId, index) => ({ id: `w-${index + 1}`, catalogId }),
    ),
  },
]

export class MockBoardStore implements BoardStore {
  private boards: Board[]
  private nextId = 2

  constructor(boards: Board[] = seed()) {
    this.boards = boards
  }

  private find(id: string) {
    const board = this.boards.find((candidate) => candidate.id === id)
    if (!board) throw new Error(`Board ${id} not found`)
    return board
  }

  async list() {
    return this.boards.map((board) => ({ ...board, widgets: [...board.widgets] }))
  }

  async create(name: string) {
    const board = { id: `board-${this.nextId++}`, name, widgets: [] }
    this.boards.push(board)
    return { ...board }
  }

  async rename(id: string, name: string) {
    this.find(id).name = name
  }

  async remove(id: string) {
    this.find(id)
    this.boards = this.boards.filter((board) => board.id !== id)
  }

  async saveWidgets(id: string, widgets: BoardWidget[]) {
    this.find(id).widgets = [...widgets]
  }
}
