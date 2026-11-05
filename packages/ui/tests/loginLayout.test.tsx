import { fireEvent, render, screen } from '@testing-library/react'
import { LoginLayout, UiProvider, workspacePalette } from '../src'

const show = (onSubmit = vi.fn(), error?: string) =>
  render(
    <UiProvider palette={workspacePalette}>
      <LoginLayout
        background={<div data-testid="background" />}
        logo={<svg data-testid="logo" />}
        name="Sami Workspace"
        tagline="Plan. Order. Deliver."
        title="Sign in to Sami Workspace"
        error={error}
        onSubmit={onSubmit}
        footer={<button type="button">Sign in with Microsoft</button>}
      />
    </UiProvider>,
  )

describe('LoginLayout', () => {
  it('shows the background, logo, name, tagline and the sign-in card', () => {
    show()
    expect(screen.getByTestId('background')).toBeInTheDocument()
    expect(screen.getByTestId('logo')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Sami Workspace' })).toBeInTheDocument()
    expect(screen.getByText('Plan. Order. Deliver.')).toBeInTheDocument()
    expect(screen.getByText('Sign in to Sami Workspace')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sign in with Microsoft' })).toBeInTheDocument()
  })

  it('sends the typed email and password', () => {
    const onSubmit = vi.fn()
    show(onSubmit)
    fireEvent.change(screen.getByLabelText(/work email/i), { target: { value: 'a@b.co' } })
    fireEvent.change(screen.getByLabelText(/^password/i), { target: { value: 'secret' } })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(onSubmit).toHaveBeenCalledWith('a@b.co', 'secret')
  })

  it('shows a problem line', () => {
    show(vi.fn(), 'Incorrect email or password')
    expect(screen.getByRole('alert')).toHaveTextContent('Incorrect email or password')
  })
})
