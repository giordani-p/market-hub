import { useState, type FormEvent } from 'react'
import { useAuth } from '../../app/providers/auth-context'
import { Button } from '../../components/ui/Button'
import { TextField } from '../../components/ui/TextField'
import { ApiRequestError } from '../../lib/api/client'
import styles from './LoginPage.module.css'

export function LoginPage() {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email, password)
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.code === 'unauthorized' ? 'Email ou senha inválidos.' : err.message)
      } else {
        setError('Não foi possível conectar à API.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className={styles.loginPage}>
      <form className={styles.card} onSubmit={handleSubmit}>
        <div className={styles.brand}>
          <h1 className={styles.title}>Market Hub</h1>
          <p className={styles.subtitle}>Entre para acompanhar seus pedidos.</p>
        </div>
        <TextField
          label="Email"
          type="email"
          name="email"
          autoComplete="username"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
        />
        <TextField
          label="Senha"
          type="password"
          name="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />
        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
        <Button type="submit" loading={submitting} fullWidth>
          Entrar
        </Button>
      </form>
    </div>
  )
}
