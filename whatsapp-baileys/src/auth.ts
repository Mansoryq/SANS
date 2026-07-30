import { initAuthCreds, BufferJSON } from '@whiskeysockets/baileys'
import { Pool } from 'pg'

export const usePgAuthState = async (pool: Pool, session_name: string) => {
    await pool.query(`
        CREATE TABLE IF NOT EXISTS baileys_auth (
            id SERIAL PRIMARY KEY,
            session_name VARCHAR(255) NOT NULL,
            key_name VARCHAR(255) NOT NULL,
            key_value JSONB NOT NULL,
            UNIQUE (session_name, key_name)
        )
    `)

    const readData = async (key_name: string) => {
        const res = await pool.query(
            'SELECT key_value FROM baileys_auth WHERE session_name = $1 AND key_name = $2',
            [session_name, key_name]
        )
        if (res.rowCount && res.rowCount > 0) {
            return JSON.parse(JSON.stringify(res.rows[0].key_value), BufferJSON.reviver)
        }
        return null
    }

    const writeData = async (key_name: string, data: any) => {
        const json = JSON.stringify(data, BufferJSON.replacer)
        await pool.query(
            `INSERT INTO baileys_auth (session_name, key_name, key_value) 
             VALUES ($1, $2, $3)
             ON CONFLICT (session_name, key_name) 
             DO UPDATE SET key_value = EXCLUDED.key_value`,
            [session_name, key_name, json]
        )
    }

    const removeData = async (key_name: string) => {
        await pool.query(
            'DELETE FROM baileys_auth WHERE session_name = $1 AND key_name = $2',
            [session_name, key_name]
        )
    }

    let creds = await readData('creds')
    if (!creds) {
        creds = initAuthCreds()
        await writeData('creds', creds)
    }

    return {
        state: {
            creds,
            keys: {
                get: async (type: string, ids: string[]) => {
                    const data: { [key: string]: any } = {}
                    await Promise.all(
                        ids.map(async (id) => {
                            let value = await readData(`${type}-${id}`)
                            if (type === 'app-state-sync-key' && value) {
                                value = Buffer.from(value.data || value)
                            }
                            if (value) {
                                data[id] = value
                            }
                        })
                    )
                    return data
                },
                set: async (data: any) => {
                    const tasks: Promise<any>[] = []
                    for (const category in data) {
                        for (const id in data[category]) {
                            const value = data[category][id]
                            const key = `${category}-${id}`
                            if (value) {
                                tasks.push(writeData(key, value))
                            } else {
                                tasks.push(removeData(key))
                            }
                        }
                    }
                    await Promise.all(tasks)
                }
            }
        },
        saveCreds: () => {
            return writeData('creds', creds)
        }
    }
}

export const clearPgAuthState = async (pool: Pool, session_name: string) => {
    await pool.query('DELETE FROM baileys_auth WHERE session_name = $1', [session_name])
}
